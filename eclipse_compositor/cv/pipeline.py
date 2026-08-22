"""End-to-end process: detect → crop → layout → composite."""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from eclipse_compositor.cv.colorimetry import apply_colorimetry
from eclipse_compositor.cv.compositing import (
    create_canvas,
    paste_lighten,
    save_image,
)
from eclipse_compositor.cv.cropping import crop_around_center
from eclipse_compositor.cv.detection import DiscDetection, find_disc_center
from eclipse_compositor.cv.layout import (
    LayoutDirection,
    LayoutType,
    canvas_size_from_positions,
    generate_positions,
    normalize_positions,
)
from eclipse_compositor.cv.loading import load_image_bgr
from eclipse_compositor.cv.masking import apply_circular_mask, circular_fade_alpha

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessedFrame:
    """A successfully aligned and cropped eclipse frame."""

    path: Path
    crop: np.ndarray
    detection: DiscDetection


@dataclass(frozen=True)
class ComposeParams:
    """Parameters controlling detection, crop, and layout."""

    crop_size: int = 800
    spacing: float = -0.15
    layout: LayoutType = LayoutType.ARC
    arc_angle: float = 120.0
    direction: LayoutDirection = LayoutDirection.HORIZONTAL
    threshold: int = 180
    # Extra pixels around the layout; negative values crop into the frames.
    margin_x: int = 40
    margin_y: int = 40
    # Expand crop so corona / diamond ring is not clipped (× enclosing diameter).
    radius_margin: float = 2.6
    grid_columns: int = 3
    grid_rows: int = 2
    # Color grade applied once to the finished composite (1.0 / 0 = identity).
    contrast: float = 1.0
    saturation: float = 1.0
    brightness: float = 0.0
    gamma: float = 1.0
    temperature: float = 0.0
    # Per-frame circular fade; disabled leaves the hard square crop.
    mask_enabled: bool = False
    mask_size: float = 0.90
    mask_feather: float = 0.20
    manual_detections: dict[Path, DiscDetection] | None = None


def process_frame(
    path: Path | str,
    image: np.ndarray | None = None,
    *,
    crop_size: int = 800,
    threshold: int = 180,
) -> ProcessedFrame | None:
    """Detect the disc and return a standardized square crop.

    Args:
        path: Source file path (for logging / identity).
        image: Optional preloaded BGR image; loaded from *path* if omitted.
        crop_size: Output square side length.
        threshold: Brightness threshold for disc isolation.

    Returns:
        ``ProcessedFrame`` or ``None`` if detection fails (logged and skipped).
    """
    path = Path(path)
    try:
        bgr = image if image is not None else load_image_bgr(path)
    except FileNotFoundError as exc:
        logger.warning("Skipping %s: %s", path, exc)
        return None

    detection = find_disc_center(bgr, threshold=threshold)
    if detection is None:
        logger.warning("Skipping %s: disc not found (threshold=%d)", path.name, threshold)
        return None

    crop = crop_around_center(bgr, detection.center, crop_size)
    return ProcessedFrame(path=path, crop=crop, detection=detection)


def effective_crop_size(detections: list[DiscDetection], params: ComposeParams) -> int:
    """Choose a shared crop large enough for the widest luminous disc.

    Uses ``max(user crop_size, 2 * max_radius * radius_margin)`` so totality /
    diamond-ring frames keep their corona inside the square.
    """
    if not detections:
        return max(1, params.crop_size)
    max_radius = max(d.radius for d in detections)
    from_radius = int(math.ceil(2.0 * max_radius * params.radius_margin))
    return max(params.crop_size, from_radius, 1)


def compose_frames(
    frames: list[ProcessedFrame],
    params: ComposeParams,
    frame_size: int | None = None,
) -> np.ndarray:
    """Layout and lighten-blend processed crops onto a single canvas.

    Colorimetry is applied per crop (so the black canvas stays black), then
    an optional circular fade-to-black mask softens square crop edges before
    the lighten blend.

    Args:
        frames: Detected and cropped frames in display order.
        params: Layout, grade, and mask parameters.
        frame_size: Square side length of each crop (defaults to ``params.crop_size``).

    Returns:
        Composited BGR image. Empty 1x1 canvas if *frames* is empty.
    """
    if not frames:
        return create_canvas(1, 1)

    size = frame_size if frame_size is not None else params.crop_size
    raw_positions = generate_positions(
        layout=params.layout,
        count=len(frames),
        frame_size=size,
        spacing=params.spacing,
        arc_angle=params.arc_angle,
        direction=params.direction,
        grid_columns=params.grid_columns,
        grid_rows=params.grid_rows,
    )
    positions = normalize_positions(
        raw_positions, margin_x=params.margin_x, margin_y=params.margin_y
    )
    width, height = canvas_size_from_positions(
        raw_positions,
        size,
        margin_x=params.margin_x,
        margin_y=params.margin_y,
    )
    canvas = create_canvas(width, height)
    alpha = (
        circular_fade_alpha(size, params.mask_size, params.mask_feather)
        if params.mask_enabled
        else None
    )

    for frame, pos in zip(frames, positions, strict=True):
        patch = apply_colorimetry(
            frame.crop,
            contrast=params.contrast,
            saturation=params.saturation,
            brightness=params.brightness,
            gamma=params.gamma,
            temperature=params.temperature,
        )
        if alpha is not None:
            patch = apply_circular_mask(patch, alpha)
        paste_lighten(canvas, patch, pos)
    return canvas


def compose_sequence(
    paths: list[Path],
    params: ComposeParams,
    images: dict[Path, np.ndarray] | None = None,
    *,
    on_progress: Callable[[float, str], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> tuple[np.ndarray, list[Path], list[Path]]:
    """Full pipeline over an ordered list of source paths.

    Detection runs first so crop size can expand to fit the largest disc /
    corona envelope; paths are processed in the given order (manual gallery order).

    Args:
        paths: Image paths in composite order (enabled frames only).
        params: Detection and layout parameters.
        images: Optional path→BGR cache (proxies or full-res).
        on_progress: Optional ``(fraction, message)`` callback.
        should_cancel: When this returns True, raise ``InterruptedError``.

    Returns:
        Tuple of ``(composite, used_paths, skipped_paths)``.
    """
    used: list[Path] = []
    skipped: list[Path] = []
    loaded: list[tuple[Path, np.ndarray, DiscDetection]] = []
    total = max(1, len(paths))

    for i, path in enumerate(paths):
        if should_cancel is not None and should_cancel():
            raise InterruptedError("Cancelled")
        if on_progress is not None:
            on_progress(i / total, f"Processing {path.name}…")
        try:
            bgr = images[path] if images and path in images else load_image_bgr(path)
        except FileNotFoundError as exc:
            logger.warning("Skipping %s: %s", path, exc)
            skipped.append(path)
            continue

        detection = None
        if params.manual_detections is not None:
            detection = params.manual_detections.get(path)
        if detection is None:
            detection = find_disc_center(bgr, threshold=params.threshold)
        if detection is None:
            logger.warning(
                "Skipping %s: disc not found (threshold=%d)", path.name, params.threshold
            )
            skipped.append(path)
            continue
        loaded.append((path, bgr, detection))
        used.append(path)

    if not loaded:
        return create_canvas(1, 1), used, skipped

    if should_cancel is not None and should_cancel():
        raise InterruptedError("Cancelled")

    crop_size = effective_crop_size([d for _, _, d in loaded], params)
    if crop_size > params.crop_size:
        logger.info(
            "Expanding crop size %d → %d to fit corona / diamond ring",
            params.crop_size,
            crop_size,
        )

    frames: list[ProcessedFrame] = []
    for path, bgr, detection in loaded:
        if should_cancel is not None and should_cancel():
            raise InterruptedError("Cancelled")
        crop = crop_around_center(bgr, detection.center, crop_size)
        frames.append(ProcessedFrame(path=path, crop=crop, detection=detection))

    if on_progress is not None:
        on_progress(0.92, "Compositing…")
    # Layout must use the effective crop size, not the pre-expansion slider value.
    layout_params = replace(params, crop_size=crop_size)
    composite = compose_frames(frames, layout_params, frame_size=crop_size)
    return composite, used, skipped


def export_composite(
    paths: list[Path],
    params: ComposeParams,
    output_path: Path | str,
    *,
    on_progress: Callable[[float, str], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> tuple[np.ndarray, list[Path], list[Path]]:
    """Run the full-resolution pipeline and write the result to disk.

    Args:
        paths: Enabled source paths in order.
        params: Compose parameters.
        output_path: Destination file (.jpg / .tif / .png).
        on_progress: Optional ``(fraction, message)`` callback.
        should_cancel: When this returns True, raise ``InterruptedError``.

    Returns:
        Same tuple as ``compose_sequence``.
    """
    dest = Path(output_path)

    def _progress(fraction: float, message: str) -> None:
        if on_progress is not None:
            on_progress(fraction, message)

    composite, used, skipped = compose_sequence(
        paths,
        params,
        on_progress=lambda p, m: _progress(0.9 * p, m),
        should_cancel=should_cancel,
    )
    if should_cancel is not None and should_cancel():
        raise InterruptedError("Cancelled")
    _progress(0.94, f"Writing {dest.name}…")
    save_image(str(dest), composite)
    _progress(1.0, f"Saved {dest.name}")
    return composite, used, skipped
