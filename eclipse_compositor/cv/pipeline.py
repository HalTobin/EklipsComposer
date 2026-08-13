"""End-to-end process: detect → crop → layout → composite."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from eclipse_compositor.cv.compositing import (
    create_canvas,
    paste_lighten,
    save_image,
)
from eclipse_compositor.cv.cropping import crop_around_center
from eclipse_compositor.cv.detection import DiscDetection, find_disc_center
from eclipse_compositor.cv.layout import (
    LayoutType,
    canvas_size_from_positions,
    generate_positions,
    normalize_positions,
)
from eclipse_compositor.cv.loading import load_image_bgr

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
    curvature: float = 0.35
    threshold: int = 180
    padding: int = 40
    # Expand crop so corona / diamond ring is not clipped (× enclosing diameter).
    radius_margin: float = 2.6
    grid_columns: int = 3
    grid_rows: int = 2


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

    Args:
        frames: Detected and cropped frames in display order.
        params: Layout / padding parameters.
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
        curvature=params.curvature,
        grid_columns=params.grid_columns,
        grid_rows=params.grid_rows,
    )
    positions = normalize_positions(raw_positions, padding=params.padding)
    width, height = canvas_size_from_positions(
        raw_positions, size, padding=params.padding
    )
    canvas = create_canvas(width, height)

    for frame, pos in zip(frames, positions, strict=True):
        paste_lighten(canvas, frame.crop, pos)
    return canvas


def compose_sequence(
    paths: list[Path],
    params: ComposeParams,
    images: dict[Path, np.ndarray] | None = None,
) -> tuple[np.ndarray, list[Path], list[Path]]:
    """Full pipeline over an ordered list of source paths.

    Detection runs first so crop size can expand to fit the largest disc /
    corona envelope; paths are processed in the given order (manual gallery order).

    Args:
        paths: Image paths in composite order (enabled frames only).
        params: Detection and layout parameters.
        images: Optional path→BGR cache (proxies or full-res).

    Returns:
        Tuple of ``(composite, used_paths, skipped_paths)``.
    """
    used: list[Path] = []
    skipped: list[Path] = []
    loaded: list[tuple[Path, np.ndarray, DiscDetection]] = []

    for path in paths:
        try:
            bgr = images[path] if images and path in images else load_image_bgr(path)
        except FileNotFoundError as exc:
            logger.warning("Skipping %s: %s", path, exc)
            skipped.append(path)
            continue

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

    crop_size = effective_crop_size([d for _, _, d in loaded], params)
    if crop_size > params.crop_size:
        logger.info(
            "Expanding crop size %d → %d to fit corona / diamond ring",
            params.crop_size,
            crop_size,
        )

    frames: list[ProcessedFrame] = []
    for path, bgr, detection in loaded:
        crop = crop_around_center(bgr, detection.center, crop_size)
        frames.append(ProcessedFrame(path=path, crop=crop, detection=detection))

    # Layout must use the effective crop size, not the pre-expansion slider value.
    layout_params = ComposeParams(
        crop_size=crop_size,
        spacing=params.spacing,
        layout=params.layout,
        curvature=params.curvature,
        threshold=params.threshold,
        padding=params.padding,
        radius_margin=params.radius_margin,
        grid_columns=params.grid_columns,
        grid_rows=params.grid_rows,
    )
    composite = compose_frames(frames, layout_params, frame_size=crop_size)
    return composite, used, skipped


def export_composite(
    paths: list[Path],
    params: ComposeParams,
    output_path: Path | str,
) -> tuple[np.ndarray, list[Path], list[Path]]:
    """Run the full-resolution pipeline and write the result to disk.

    Args:
        paths: Enabled source paths in order.
        params: Compose parameters.
        output_path: Destination file (.jpg / .tif / .png).

    Returns:
        Same tuple as ``compose_sequence``.
    """
    composite, used, skipped = compose_sequence(paths, params)
    save_image(str(output_path), composite)
    return composite, used, skipped
