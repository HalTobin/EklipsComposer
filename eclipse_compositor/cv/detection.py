"""Solar/lunar disc detection via thresholding and image moments."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from eclipse_compositor.cv.ops import (
    bgr_to_gray,
    gaussian_blur_5,
    hull_perimeter,
    largest_blob_geometry,
    min_enclosing_circle,
    morph_open_close,
    polygon_area_centroid,
    threshold_binary,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiscDetection:
    """Result of locating the bright disc in a frame.

    Attributes:
        center: (x, y) center in image coordinates.
        radius: Approximate luminous radius in pixels (enclosing circle).
        area: Contour / mask area in pixels.
        confidence: Heuristic score in [0, 1].
    """

    center: tuple[int, int]
    radius: float
    area: float
    confidence: float


def _mask_from_threshold(
    blurred: np.ndarray,
    threshold: int,
    invert: bool,
) -> np.ndarray:
    mask = threshold_binary(blurred, threshold, invert=invert)
    return morph_open_close(mask)


def _detection_from_mask(
    mask: np.ndarray,
    min_area: float,
) -> DiscDetection | None:
    """Build a DiscDetection from a binary mask.

    Uses the largest blob's convex hull and min-enclosing circle so crescent
    and diamond-ring frames still yield a stable lunar/solar center instead of
    latching onto a single bright Baily's bead.
    """
    geom = largest_blob_geometry(mask)
    if geom is None:
        return None
    hull, area = geom
    if area < min_area:
        return None

    # Convex-hull centroid so a dark lunar disc inside a diamond-ring / corona
    # does not pull the center of mass toward the bright bead.
    hull_area, cx_f, cy_f = polygon_area_centroid(hull)
    if hull_area <= 0:
        return None
    cx = int(round(cx_f))
    cy = int(round(cy_f))
    (_ecx, _ecy), radius = min_enclosing_circle(hull)
    radius = float(radius)
    if radius < 1.0:
        return None

    perimeter = hull_perimeter(hull)
    circularity = 0.0
    if perimeter > 0:
        circularity = float(4.0 * np.pi * hull_area / (perimeter * perimeter))
        circularity = max(0.0, min(1.0, circularity))

    h, w = mask.shape[:2]
    area_ratio = min(1.0, area / (0.25 * h * w))
    confidence = 0.55 * circularity + 0.45 * area_ratio

    return DiscDetection(
        center=(cx, cy),
        radius=radius,
        area=area,
        confidence=confidence,
    )


def find_disc_center(
    image: np.ndarray,
    threshold: int = 180,
    invert: bool = False,
    min_area_fraction: float = 1e-4,
) -> DiscDetection | None:
    """Locate the solar/lunar disc using thresholding + moments.

    Tries the user threshold first, then lower fallbacks so totality / diamond-
    ring frames (tiny bright bead + faint corona) still resolve to the full
    luminous envelope rather than clipping the ring.

    Args:
        image: BGR or grayscale source image.
        threshold: Primary binary threshold in [0, 255].
        invert: If True, treat the darkest blob as the disc.
        min_area_fraction: Minimum blob area as a fraction of the image.

    Returns:
        ``DiscDetection`` on success, or ``None`` if no reliable disc is found.
    """
    gray = bgr_to_gray(image) if image.ndim == 3 else image
    blurred = gaussian_blur_5(gray)
    h, w = gray.shape[:2]
    min_area = max(1.0, min_area_fraction * h * w)

    # Fallbacks capture faint corona around totality / diamond ring.
    candidates_thresh = []
    for t in (threshold, max(40, threshold - 60), max(30, threshold // 2), 40):
        if t not in candidates_thresh:
            candidates_thresh.append(t)

    detections: list[DiscDetection] = []
    for t in candidates_thresh:
        mask = _mask_from_threshold(blurred, t, invert=invert)
        det = _detection_from_mask(mask, min_area=min_area)
        if det is not None:
            detections.append(det)

    if not detections:
        logger.warning(
            "Disc detection failed: no contours for thresholds=%s", candidates_thresh
        )
        return None

    # Prefer the most circular mid/large disc; break ties by larger radius so we
    # do not keep a diamond-bead-sized blob when a corona envelope exists.
    best = max(
        detections,
        key=lambda d: (d.confidence * 0.7 + min(1.0, d.radius / (0.35 * max(h, w))) * 0.3, d.radius),
    )

    # If the top-confidence hit is tiny vs another candidate, the bright bead
    # won — switch to the largest-radius candidate with acceptable confidence.
    max_radius = max(d.radius for d in detections)
    if best.radius < 0.55 * max_radius:
        larger = [d for d in detections if d.radius >= 0.85 * max_radius]
        if larger:
            best = max(larger, key=lambda d: (d.confidence, d.radius))
            logger.info(
                "Disc detection: preferring larger envelope (r=%.1f) over bead-sized hit",
                best.radius,
            )

    return best
