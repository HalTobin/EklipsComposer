"""Canvas blending for overlapping eclipse discs (lighten / max)."""

from __future__ import annotations

import numpy as np

from eclipse_compositor.cv.ops import save_bgr


def create_canvas(width: int, height: int, channels: int = 3) -> np.ndarray:
    """Allocate a black BGR canvas.

    Args:
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        channels: Number of color channels (default 3).

    Returns:
        Zero-initialized uint8 array.
    """
    return np.zeros((height, width, channels), dtype=np.uint8)


def paste_lighten(
    canvas: np.ndarray,
    patch: np.ndarray,
    top_left: tuple[int, int],
) -> None:
    """Composite *patch* onto *canvas* with a lighten (per-pixel max) blend.

    Ideal for overlapping solar coronas / discs: brighter pixels win.
    Clips automatically at canvas borders.

    Args:
        canvas: Destination BGR image (modified in place).
        patch: Source BGR crop to blend.
        top_left: (x, y) where the patch's top-left should land.
    """
    x, y = top_left
    ph, pw = patch.shape[:2]
    ch, cw = canvas.shape[:2]

    src_x0 = max(0, -x)
    src_y0 = max(0, -y)
    dst_x0 = max(0, x)
    dst_y0 = max(0, y)
    dst_x1 = min(cw, x + pw)
    dst_y1 = min(ch, y + ph)

    if dst_x1 <= dst_x0 or dst_y1 <= dst_y0:
        return

    src_x1 = src_x0 + (dst_x1 - dst_x0)
    src_y1 = src_y0 + (dst_y1 - dst_y0)

    roi = canvas[dst_y0:dst_y1, dst_x0:dst_x1]
    src = patch[src_y0:src_y1, src_x0:src_x1]
    np.maximum(roi, src, out=roi)


def save_image(path: str, image: np.ndarray, jpeg_quality: int = 95) -> None:
    """Write *image* to disk (format inferred from extension).

    Args:
        path: Output file path (.jpg / .tif / .png, etc.).
        image: BGR uint8 array.
        jpeg_quality: JPEG quality when applicable (0–100).
    """
    try:
        save_bgr(path, image, jpeg_quality=jpeg_quality)
    except OSError as exc:
        raise OSError(f"Failed to write image: {path}") from exc
