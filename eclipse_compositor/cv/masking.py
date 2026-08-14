"""Circular fade-to-black masks for softening square crop edges."""

from __future__ import annotations

import numpy as np


def circular_fade_alpha(
    size: int,
    radius: float,
    feather: float,
) -> np.ndarray:
    """Build a centered circular alpha map that falls off to black.

    Distance is measured from the crop center. *radius* is the outer edge
    of the fade (alpha = 0) as a fraction of half the square side (1.0
    touches the mid-sides; ``sqrt(2)`` reaches the corners). *feather* is
    the radial width of the 1→0 transition, also as a fraction of half
    the side. Inside ``radius - feather`` the image stays fully opaque.

    Args:
        size: Square side length in pixels.
        radius: Outer mask radius (fraction of half-side, typically 0.4–1.5).
        feather: Gradient width (fraction of half-side, 0 = hard circle).

    Returns:
        Float32 array of shape ``(size, size)`` with values in ``[0, 1]``.
    """
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")

    half = size / 2.0
    outer = max(0.0, float(radius)) * half
    inner = max(0.0, outer - max(0.0, float(feather)) * half)

    yy, xx = np.ogrid[:size, :size]
    # Pixel centers so a radius of 1.0 lands on the mid-side pixels.
    dist = np.sqrt((xx + 0.5 - half) ** 2 + (yy + 0.5 - half) ** 2).astype(np.float32)

    if outer <= inner:
        return (dist <= outer).astype(np.float32)

    alpha = (outer - dist) / (outer - inner)
    return np.clip(alpha, 0.0, 1.0).astype(np.float32)


def apply_circular_mask(
    image: np.ndarray,
    alpha: np.ndarray,
) -> np.ndarray:
    """Multiply *image* by *alpha*, fading edges to pitch black.

    Args:
        image: BGR (or gray) uint8 crop.
        alpha: Float32 map matching the spatial size of *image*.

    Returns:
        New uint8 array; *image* is not modified.
    """
    if image.shape[:2] != alpha.shape[:2]:
        raise ValueError(
            f"alpha shape {alpha.shape} does not match image {image.shape[:2]}"
        )
    scale = alpha if image.ndim == 2 else alpha[..., None]
    return np.clip(np.rint(image.astype(np.float32) * scale), 0, 255).astype(np.uint8)
