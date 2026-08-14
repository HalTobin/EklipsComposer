"""Layout math for placing cropped discs on the composite canvas.

Layout generation is intentionally decoupled from image processing so linear,
arc, and grid placements can be swapped freely. Direction (horizontal, vertical,
diagonal) is applied as a rigid rotation so every family shares the same spacing.
"""

from __future__ import annotations

import math
from enum import Enum

import numpy as np


class LayoutType(str, Enum):
    """Composite arrangement family."""

    LINEAR = "linear"
    ARC = "arc"
    GRID = "grid"


class LayoutDirection(str, Enum):
    """Orientation of linear and arc layouts.

    Angles are clockwise in image coordinates (y increases downward):
    horizontal →, diagonal ↘, vertical ↓, diagonal ↙.
    """

    HORIZONTAL = "horizontal"
    DIAGONAL = "diagonal"
    VERTICAL = "vertical"
    DIAGONAL_REVERSE = "diagonal_reverse"


# Clockwise degrees in a y-down coordinate system.
_DIRECTION_DEGREES: dict[LayoutDirection, float] = {
    LayoutDirection.HORIZONTAL: 0.0,
    LayoutDirection.DIAGONAL: 45.0,
    LayoutDirection.VERTICAL: 90.0,
    LayoutDirection.DIAGONAL_REVERSE: 135.0,
}

# Below this sweep the circular arc is numerically a straight line.
_MIN_ARC_DEGREES = 0.5


def direction_degrees(direction: LayoutDirection) -> float:
    """Return the clockwise rotation (degrees) for *direction*."""
    return _DIRECTION_DEGREES[direction]


def linear_positions(
    count: int,
    frame_size: int,
    spacing: float,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Place frames along a horizontal line.

    Args:
        count: Number of frames.
        frame_size: Square frame side length in pixels.
        spacing: Extra gap between frames as a fraction of *frame_size*
            (0 = abutting, 0.5 = half-frame gap). Can be negative to overlap.
        origin: Top-left of the first frame.

    Returns:
        List of (x, y) top-left coordinates for each frame.
    """
    if count <= 0:
        return []
    step = frame_size * (1.0 + spacing)
    ox, oy = origin
    return [(ox + i * step, oy) for i in range(count)]


def vertical_positions(
    count: int,
    frame_size: int,
    spacing: float,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Place frames along a vertical line (top → bottom).

    Args:
        count: Number of frames.
        frame_size: Square frame side length in pixels.
        spacing: Extra gap between frames as a fraction of *frame_size*.
        origin: Top-left of the first frame.

    Returns:
        List of (x, y) top-left coordinates for each frame.
    """
    if count <= 0:
        return []
    step = frame_size * (1.0 + spacing)
    ox, oy = origin
    return [(ox, oy + i * step) for i in range(count)]


def arc_positions(
    count: int,
    frame_size: int,
    spacing: float,
    arc_angle: float = 120.0,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Place frames at equal arc-length on a circular arc.

    Equal angular steps on a circle give constant centre-to-centre distance,
    so discs at the corners and at the bottom of the bow appear evenly spaced.
    *arc_angle* is the signed sweep in degrees (−180…180): magnitude is the
    bow size (0 = line, 180 = semicircle); the sign flips the bow
    (positive = downward smile, negative = upward frown).

    Args:
        count: Number of frames.
        frame_size: Square frame side length in pixels.
        spacing: Path gap fraction (same semantics as linear).
        arc_angle: Signed sweep in degrees, clamped to [−180, 180].
        origin: Anchor applied after the arc is generated.

    Returns:
        List of (x, y) top-left coordinates for each frame.
    """
    if count <= 0:
        return []
    if count == 1:
        return [origin]

    theta_deg = max(-180.0, min(180.0, float(arc_angle)))
    if abs(theta_deg) < _MIN_ARC_DEGREES:
        return linear_positions(count, frame_size, spacing, origin)

    step = frame_size * (1.0 + spacing)
    abs_theta = math.radians(abs(theta_deg))
    total_arc = step * (count - 1)
    radius = total_arc / abs_theta
    half = abs_theta / 2.0
    sign = 1.0 if theta_deg >= 0.0 else -1.0
    ox, oy = origin

    positions: list[tuple[float, float]] = []
    for i in range(count):
        t = i / (count - 1)
        phi = -half + t * abs_theta
        # Image y increases downward: +cos puts the bow below the chord.
        x = radius * math.sin(phi)
        y = sign * radius * math.cos(phi)
        positions.append((ox + x, oy + y))
    return positions


def grid_positions(
    count: int,
    frame_size: int,
    spacing: float,
    columns: int = 3,
    rows: int = 1,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Place frames in a row-major grid.

    Uses at least ``rows`` × ``columns`` cells. If *count* exceeds that, extra
    rows are added so no frame is dropped.

    Args:
        count: Number of frames.
        frame_size: Square frame side length in pixels.
        spacing: Gap fraction between neighboring cells.
        columns: Number of columns (lines across).
        rows: Requested number of rows (minimum).
        origin: Top-left of the first cell.

    Returns:
        List of (x, y) top-left coordinates for each frame.
    """
    if count <= 0:
        return []
    cols = max(1, int(columns))
    needed_rows = int(math.ceil(count / cols))
    _rows = max(1, int(rows), needed_rows)
    step = frame_size * (1.0 + spacing)
    ox, oy = origin

    positions: list[tuple[float, float]] = []
    for i in range(count):
        r, c = divmod(i, cols)
        if r >= _rows:
            break
        positions.append((ox + c * step, oy + r * step))
    return positions


def rotate_positions(
    positions: list[tuple[float, float]],
    angle_deg: float,
    pivot: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Rotate *positions* clockwise by *angle_deg* around *pivot* (y-down).

    The standard 2D rotation formula is clockwise in image coordinates because
    y increases downward, which maps 45° → ↘, 90° → ↓, 135° → ↙.
    """
    if not positions or abs(angle_deg) < 1e-9:
        return positions
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    px, py = pivot
    rotated: list[tuple[float, float]] = []
    for x, y in positions:
        dx = x - px
        dy = y - py
        rotated.append((px + dx * cos_a - dy * sin_a, py + dx * sin_a + dy * cos_a))
    return rotated


def generate_positions(
    layout: LayoutType,
    count: int,
    frame_size: int,
    spacing: float,
    arc_angle: float = 120.0,
    direction: LayoutDirection = LayoutDirection.HORIZONTAL,
    grid_columns: int = 3,
    grid_rows: int = 1,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Dispatch to the selected layout function and apply *direction*.

    Args:
        layout: Arrangement family (linear, arc, or grid).
        count: Number of frames.
        frame_size: Square crop size.
        spacing: Inter-frame gap fraction.
        arc_angle: Signed circular-arc sweep in degrees (ignored unless arc).
        direction: Orientation applied to linear and arc layouts.
        grid_columns: Grid column count (ignored unless grid).
        grid_rows: Grid row count (ignored unless grid).
        origin: Layout origin.

    Returns:
        Top-left positions for each frame.
    """
    if layout == LayoutType.GRID:
        return grid_positions(
            count, frame_size, spacing, grid_columns, grid_rows, origin
        )
    if layout == LayoutType.ARC:
        positions = arc_positions(count, frame_size, spacing, arc_angle, origin)
    else:
        positions = linear_positions(count, frame_size, spacing, origin)

    angle = direction_degrees(direction)
    if abs(angle) < 1e-9:
        return positions
    return rotate_positions(positions, angle, origin)


def canvas_size_from_positions(
    positions: list[tuple[float, float]],
    frame_size: int,
    padding: int = 0,
) -> tuple[int, int]:
    """Compute canvas (width, height) that fits all placed frames.

    Args:
        positions: Top-left corners from a layout function.
        frame_size: Square frame side length.
        padding: Extra border pixels on all sides.

    Returns:
        ``(width, height)`` in pixels.
    """
    if not positions:
        side = max(1, padding * 2)
        return side, side

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    min_x = min(xs)
    min_y = min(ys)
    max_x = max(x + frame_size for x in xs)
    max_y = max(y + frame_size for y in ys)

    width = int(np.ceil(max_x - min_x)) + 2 * padding
    height = int(np.ceil(max_y - min_y)) + 2 * padding
    return max(1, width), max(1, height)


def normalize_positions(
    positions: list[tuple[float, float]],
    padding: int = 0,
) -> list[tuple[int, int]]:
    """Shift positions so the bounding box origin is at (*padding*, *padding*)."""
    if not positions:
        return []
    min_x = min(p[0] for p in positions)
    min_y = min(p[1] for p in positions)
    return [
        (int(round(x - min_x + padding)), int(round(y - min_y + padding)))
        for x, y in positions
    ]
