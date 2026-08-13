"""Layout math for placing cropped discs on the composite canvas.

Layout generation is intentionally decoupled from image processing so linear,
vertical, arc, and grid placements can be swapped freely.
"""

from __future__ import annotations

import math
from enum import Enum

import numpy as np


class LayoutType(str, Enum):
    """Composite arrangement of eclipse phases."""

    LINEAR = "linear"
    VERTICAL = "vertical"
    ARC = "arc"
    GRID = "grid"


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
    curvature: float = 0.35,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Place frames along a gentle downward arc (sine-based).

    The arc spans horizontally like the linear layout; vertical offset follows
    ``sin(pi * t)`` scaled by *curvature* * total span, producing a classic
    eclipse-sequence bow.

    Args:
        count: Number of frames.
        frame_size: Square frame side length in pixels.
        spacing: Horizontal gap fraction (same semantics as linear).
        curvature: Vertical bow depth as a fraction of the horizontal span.
            0 degenerates to a straight line.
        origin: Anchor for the leftmost frame's top-left before bow offset.

    Returns:
        List of (x, y) top-left coordinates for each frame.
    """
    if count <= 0:
        return []
    if count == 1:
        return [origin]

    step = frame_size * (1.0 + spacing)
    span = step * (count - 1)
    amplitude = curvature * span
    ox, oy = origin

    positions: list[tuple[float, float]] = []
    for i in range(count):
        t = i / (count - 1)
        x = ox + i * step
        y = oy + amplitude * float(np.sin(np.pi * t))
        positions.append((x, y))
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


def generate_positions(
    layout: LayoutType,
    count: int,
    frame_size: int,
    spacing: float,
    curvature: float = 0.35,
    grid_columns: int = 3,
    grid_rows: int = 1,
    origin: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """Dispatch to the selected layout function.

    Args:
        layout: Arrangement mode.
        count: Number of frames.
        frame_size: Square crop size.
        spacing: Inter-frame gap fraction.
        curvature: Arc bow depth (ignored unless arc).
        grid_columns: Grid column count (ignored unless grid).
        grid_rows: Grid row count (ignored unless grid).
        origin: Layout origin.

    Returns:
        Top-left positions for each frame.
    """
    if layout == LayoutType.ARC:
        return arc_positions(count, frame_size, spacing, curvature, origin)
    if layout == LayoutType.VERTICAL:
        return vertical_positions(count, frame_size, spacing, origin)
    if layout == LayoutType.GRID:
        return grid_positions(
            count, frame_size, spacing, grid_columns, grid_rows, origin
        )
    return linear_positions(count, frame_size, spacing, origin)


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
