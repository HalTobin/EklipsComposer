"""Per-frame color grade applied before compositing onto the black canvas."""

from __future__ import annotations

import numpy as np

_EPS = 1e-6

# BT.601 luma weights matching ``ops.bgr_to_gray`` (OpenCV BGR order).
_LUMA_BGR = np.array([0.114, 0.587, 0.299], dtype=np.float32)


def is_identity_grade(
    contrast: float,
    saturation: float,
    brightness: float,
    gamma: float,
    temperature: float,
) -> bool:
    """True when every slider is at its photographic default (no-op)."""
    return (
        abs(contrast - 1.0) < _EPS
        and abs(saturation - 1.0) < _EPS
        and abs(brightness) < _EPS
        and abs(gamma - 1.0) < _EPS
        and abs(temperature) < _EPS
    )


def apply_colorimetry(
    image: np.ndarray,
    *,
    contrast: float = 1.0,
    saturation: float = 1.0,
    brightness: float = 0.0,
    gamma: float = 1.0,
    temperature: float = 0.0,
) -> np.ndarray:
    """Grade a BGR uint8 image in photographic order.

    Order: temperature → brightness → contrast → gamma → saturation.
    Gamma uses ``in ** (1/gamma)`` so values above 1.0 lift midtones
    (useful for revealing faint corona). Temperature shifts red vs blue
    (positive = warmer).

    Args:
        image: BGR uint8 crop (or gray).
        contrast: 1.0 is unchanged; typical UI range 0.5–2.0.
        saturation: 1.0 is unchanged; 0.0 is grayscale.
        brightness: Additive offset on 0–255; typical range −100…100.
        gamma: 1.0 is unchanged; >1 lifts shadows / midtones.
        temperature: Warm/cool shift; typical range −100…100.

    Returns:
        Graded uint8 image. Returns *image* unchanged when all defaults.
    """
    if is_identity_grade(contrast, saturation, brightness, gamma, temperature):
        return image

    work = image.astype(np.float32)

    if abs(temperature) >= _EPS and work.ndim == 3:
        shift = float(temperature) * 0.35
        work[:, :, 2] += shift  # red (BGR)
        work[:, :, 0] -= shift  # blue

    if abs(brightness) >= _EPS:
        work += float(brightness)

    if abs(contrast - 1.0) >= _EPS:
        work = (work - 128.0) * float(contrast) + 128.0

    if abs(gamma - 1.0) >= _EPS:
        safe_gamma = max(float(gamma), 0.05)
        work = np.clip(work, 0.0, 255.0)
        work = np.power(work / 255.0, 1.0 / safe_gamma) * 255.0

    if abs(saturation - 1.0) >= _EPS and work.ndim == 3:
        gray = work @ _LUMA_BGR
        sat = float(saturation)
        work = gray[..., None] * (1.0 - sat) + work * sat

    return np.clip(np.rint(work), 0, 255).astype(np.uint8)
