"""Standardized square crops centered on the detected disc."""

from __future__ import annotations

import numpy as np

from eclipse_compositor.cv.ops import resize_hw


def crop_around_center(
    image: np.ndarray,
    center: tuple[int, int],
    crop_size: int,
) -> np.ndarray:
    """Extract a square crop of *crop_size* centered on *center*.

    Pads with black if the crop window extends past image borders so every
    frame shares an identical output shape for compositing.

    Args:
        image: BGR source image.
        center: (x, y) disc center in image coordinates.
        crop_size: Desired square side length in pixels (must be > 0).

    Returns:
        BGR image of shape ``(crop_size, crop_size, 3)``.
    """
    if crop_size <= 0:
        raise ValueError(f"crop_size must be positive, got {crop_size}")

    h, w = image.shape[:2]
    cx, cy = center
    half = crop_size // 2

    x0 = cx - half
    y0 = cy - half
    x1 = x0 + crop_size
    y1 = y0 + crop_size

    # Destination offsets when source region is clipped by borders.
    src_x0 = max(0, x0)
    src_y0 = max(0, y0)
    src_x1 = min(w, x1)
    src_y1 = min(h, y1)

    dst_x0 = src_x0 - x0
    dst_y0 = src_y0 - y0
    dst_x1 = dst_x0 + (src_x1 - src_x0)
    dst_y1 = dst_y0 + (src_y1 - src_y0)

    if image.ndim == 2:
        canvas = np.zeros((crop_size, crop_size), dtype=image.dtype)
    else:
        canvas = np.zeros((crop_size, crop_size, image.shape[2]), dtype=image.dtype)

    if src_x1 > src_x0 and src_y1 > src_y0:
        canvas[dst_y0:dst_y1, dst_x0:dst_x1] = image[src_y0:src_y1, src_x0:src_x1]
    return canvas


def scale_crop_size_for_proxy(
    full_crop_size: int,
    full_shape: tuple[int, ...],
    proxy_shape: tuple[int, ...],
) -> int:
    """Map a full-resolution crop size onto a proxy image scale.

    Args:
        full_crop_size: Crop size intended for full-res frames.
        full_shape: ``(H, W, ...)`` of the full-res image.
        proxy_shape: ``(H, W, ...)`` of the proxy image.

    Returns:
        Integer crop size for the proxy, at least 1.
    """
    full_h, full_w = full_shape[:2]
    proxy_h, proxy_w = proxy_shape[:2]
    scale = min(proxy_w / max(full_w, 1), proxy_h / max(full_h, 1))
    return max(1, int(round(full_crop_size * scale)))


def resize_square(image: np.ndarray, size: int) -> np.ndarray:
    """Resize a (near) square image to an exact *size* x *size* square."""
    if image.shape[0] == size and image.shape[1] == size:
        return image
    return resize_hw(image, size, size)
