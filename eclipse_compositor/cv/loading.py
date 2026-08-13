"""Image loading, EXIF sorting, and proxy generation."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from eclipse_compositor.cv.ops import load_bgr, resize_hw

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
)


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
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


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
