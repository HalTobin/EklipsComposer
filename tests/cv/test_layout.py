"""Unit tests for circle layout calculation in eclipse_compositor.cv.layout."""

from __future__ import annotations

import math

import pytest

from eclipse_compositor.cv.layout import (
    LayoutDirection,
    LayoutType,
    canvas_size_from_positions,
    circle_positions,
    generate_positions,
    normalize_positions,
)


class TestCirclePositions:
    """Test suite for circle_positions layout math."""

    def test_zero_or_negative_count_returns_empty(self) -> None:
        assert circle_positions(0, 800, 0.0) == []
        assert circle_positions(-5, 800, 0.0) == []

    def test_single_frame_returns_origin(self) -> None:
        assert circle_positions(1, 800, 0.0, origin=(15.0, 25.0)) == [(15.0, 25.0)]

    def test_four_frames_cardinal_positions(self) -> None:
        frame_size = 100
        spacing = 0.0
        positions = circle_positions(4, frame_size, spacing, origin=(0.0, 0.0))

        step = 100.0
        circumference = 4 * step
        radius = circumference / (2.0 * math.pi)

        assert len(positions) == 4

        # Frame 0: 12 o'clock (0, -radius)
        assert positions[0][0] == pytest.approx(0.0, abs=1e-5)
        assert positions[0][1] == pytest.approx(-radius, abs=1e-5)

        # Frame 1: 3 o'clock (radius, 0)
        assert positions[1][0] == pytest.approx(radius, abs=1e-5)
        assert positions[1][1] == pytest.approx(0.0, abs=1e-5)

        # Frame 2: 6 o'clock (0, radius)
        assert positions[2][0] == pytest.approx(0.0, abs=1e-5)
        assert positions[2][1] == pytest.approx(radius, abs=1e-5)

        # Frame 3: 9 o'clock (-radius, 0)
        assert positions[3][0] == pytest.approx(-radius, abs=1e-5)
        assert positions[3][1] == pytest.approx(0.0, abs=1e-5)

    def test_spacing_scales_radius(self) -> None:
        frame_size = 200
        count = 6

        pos_abutting = circle_positions(count, frame_size, spacing=0.0)
        pos_spaced = circle_positions(count, frame_size, spacing=0.5)

        # Distance from origin for frame 0 (at 12 o'clock, y = -radius)
        r_abutting = abs(pos_abutting[0][1])
        r_spaced = abs(pos_spaced[0][1])

        expected_r_abutting = (count * frame_size * 1.0) / (2.0 * math.pi)
        expected_r_spaced = (count * frame_size * 1.5) / (2.0 * math.pi)

        assert r_abutting == pytest.approx(expected_r_abutting, rel=1e-5)
        assert r_spaced == pytest.approx(expected_r_spaced, rel=1e-5)
        assert r_spaced == pytest.approx(r_abutting * 1.5, rel=1e-5)

    def test_origin_offset_applied(self) -> None:
        origin = (100.0, 200.0)
        positions = circle_positions(4, 100, 0.0, origin=origin)
        r = (4 * 100.0) / (2.0 * math.pi)

        assert positions[0][0] == pytest.approx(origin[0], abs=1e-5)
        assert positions[0][1] == pytest.approx(origin[1] - r, abs=1e-5)


class TestGeneratePositionsCircle:
    """Test suite for generate_positions with LayoutType.CIRCLE."""

    def test_generate_positions_circle_horizontal(self) -> None:
        positions = generate_positions(
            layout=LayoutType.CIRCLE,
            count=4,
            frame_size=100,
            spacing=0.0,
            direction=LayoutDirection.HORIZONTAL,
        )
        r = (4 * 100.0) / (2.0 * math.pi)
        assert positions[0][0] == pytest.approx(0.0, abs=1e-5)
        assert positions[0][1] == pytest.approx(-r, abs=1e-5)

    def test_generate_positions_circle_vertical_rotation(self) -> None:
        # Vertical is 90° clockwise rotation: 12 o'clock -> 3 o'clock
        positions = generate_positions(
            layout=LayoutType.CIRCLE,
            count=4,
            frame_size=100,
            spacing=0.0,
            direction=LayoutDirection.VERTICAL,
        )
        r = (4 * 100.0) / (2.0 * math.pi)
        assert positions[0][0] == pytest.approx(r, abs=1e-5)
        assert positions[0][1] == pytest.approx(0.0, abs=1e-5)

    def test_generate_positions_circle_diagonal_rotation(self) -> None:
        # Diagonal is 45° clockwise rotation: (0, -r) -> (r*sin(45°), -r*cos(45°))
        positions = generate_positions(
            layout=LayoutType.CIRCLE,
            count=4,
            frame_size=100,
            spacing=0.0,
            direction=LayoutDirection.DIAGONAL,
        )
        r = (4 * 100.0) / (2.0 * math.pi)
        expected_x = r * math.sin(math.radians(45.0))
        expected_y = -r * math.cos(math.radians(45.0))
        assert positions[0][0] == pytest.approx(expected_x, abs=1e-5)
        assert positions[0][1] == pytest.approx(expected_y, abs=1e-5)


class TestCircleCanvasSizingAndNormalization:
    """Test suite for canvas sizing and position normalization with circle layouts."""

    def test_circle_canvas_size_and_normalization(self) -> None:
        positions = generate_positions(
            layout=LayoutType.CIRCLE,
            count=4,
            frame_size=100,
            spacing=0.0,
        )
        margin_x = 40
        margin_y = 40
        width, height = canvas_size_from_positions(
            positions, 100, margin_x=margin_x, margin_y=margin_y
        )
        normalized = normalize_positions(
            positions, margin_x=margin_x, margin_y=margin_y
        )

        assert len(normalized) == 4
        # All frames must fit within [0, width - 100] and [0, height - 100]
        for nx, ny in normalized:
            assert nx >= margin_x
            assert ny >= margin_y
            assert nx + 100 <= width
            assert ny + 100 <= height
