"""Image loading, EXIF sorting, and proxy generation."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from eclipse_compositor.cv.ops import load_bgr, resize_hw, save_bgr
from eclipse_compositor.cv.video import is_supported_video

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
)


def is_supported_image(path: Path | str) -> bool:
    """Return True if *path* has a supported still-image suffix."""
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def is_importable(path: Path | str) -> bool:
    """Return True if *path* is a supported still image or video file."""
    return is_supported_image(path) or is_supported_video(path)


def image_dialog_globs() -> str:
    """Qt file-dialog glob list for supported still-image suffixes."""
    return " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))


def _is_hidden_part(path: Path) -> bool:
    """True if any path component is hidden (``.name`` / ``__MACOSX``)."""
    return any(part.startswith(".") or part == "__MACOSX" for part in path.parts)


def list_image_paths(directory: Path | str) -> list[Path]:
    """Return image file paths under *directory* (non-recursive).

    Args:
        directory: Folder containing eclipse sequence frames.

    Returns:
        Unsorted list of supported image paths.
    """
    root = Path(directory)
    if not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")
    return [
        p
        for p in root.iterdir()
        if p.is_file() and is_supported_image(p) and not _is_hidden_part(p)
    ]


def collect_import_paths(candidates: list[Path | str]) -> list[Path]:
    """Expand dropped files/folders into a de-duplicated import list.

    Top-level files keep the given order. Each directory is expanded
    recursively; still images are appended in chronological (EXIF) order
    and videos follow in filename order.

    Args:
        candidates: Files and/or directories from a file dialog or drop.

    Returns:
        Existing supported image and video paths, with duplicates (same
        resolved path) removed while preserving first-seen order.
    """
    collected: list[Path] = []
    seen: set[Path] = set()

    def _add(path: Path) -> None:
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            return
        seen.add(key)
        collected.append(path)

    for raw in candidates:
        path = Path(raw)
        if _is_hidden_part(path):
            continue
        if path.is_file() and is_importable(path):
            _add(path)
            continue
        if path.is_dir():
            found = [
                p
                for p in path.rglob("*")
                if p.is_file() and is_importable(p) and not _is_hidden_part(p)
            ]
            images = [p for p in found if is_supported_image(p)]
            videos = [p for p in found if is_supported_video(p)]
            for image in sort_chronologically(images):
                _add(image)
            for video in sorted(videos, key=lambda p: p.name.lower()):
                _add(video)
    return collected


def _exif_datetime(path: Path) -> datetime | None:
    """Extract EXIF DateTimeOriginal / DateTime if present."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            # 36867 = DateTimeOriginal, 306 = DateTime
            for tag in (36867, 306):
                raw = exif.get(tag)
                if raw:
                    return datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S")
    except Exception as exc:  # noqa: BLE001 — graceful EXIF fallback
        logger.debug("EXIF read failed for %s: %s", path, exc)
    return None


def sort_chronologically(paths: list[Path]) -> list[Path]:
    """Sort paths by EXIF capture time, falling back to filename.

    Args:
        paths: Image file paths.

    Returns:
        Chronologically ordered paths (earliest first).
    """

    def key(p: Path) -> tuple:
        dt = _exif_datetime(p)
        if dt is not None:
            return (0, dt, p.name.lower())
        return (1, p.name.lower())

    return sorted(paths, key=key)


def load_image_bgr(path: Path | str) -> np.ndarray:
    """Load an image as a BGR uint8 NumPy array via OpenCV.

    Args:
        path: Path to the image file.

    Returns:
        BGR image array of shape (H, W, 3).

    Raises:
        FileNotFoundError: If the file cannot be decoded.
    """
    path = Path(path)
    try:
        return load_bgr(path)
    except OSError as exc:
        raise FileNotFoundError(f"Failed to load image: {path}") from exc


def make_proxy(image: np.ndarray, max_edge: int = 1080) -> np.ndarray:
    """Downscale *image* so the longest edge is at most *max_edge*.

    Used for real-time UI preview; full-res sources are kept for export.

    Args:
        image: BGR source image.
        max_edge: Maximum width or height in pixels.

    Returns:
        Downscaled BGR image (or a copy if already small enough).
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_edge:
        return image.copy()
    scale = max_edge / float(longest)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return resize_hw(image, new_w, new_h)


THUMBNAIL_EDGE: int = 96


def write_thumbnail(
    image: np.ndarray,
    dest: Path | str,
    max_edge: int = THUMBNAIL_EDGE,
) -> Path:
    """Write a small JPEG thumbnail of *image* for gallery list icons.

    Downscales on the worker thread so the UI never decodes full-res
    sources just to paint a row icon.

    Args:
        image: BGR source (full-res or already-proxied).
        dest: Output JPEG path.
        max_edge: Longest thumbnail edge in pixels.

    Returns:
        The written path.
    """
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_bgr(path, make_proxy(image, max_edge=max_edge), jpeg_quality=75)
    return path
