"""Unit tests for UpdateLayoutUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState, SidebarTab
from eclipse_compositor.ui.use_cases import UpdateLayoutUseCase
from eclipse_compositor.cv.layout import LayoutType, LayoutDirection


class TestUpdateLayoutUseCase:
    """Test suite for UpdateLayoutUseCase."""

    def test_updates_layout_type(self) -> None:
        """Test updating the layout type."""
        state = ScreenState(
            layout=LayoutType.LINEAR,
        )

        next_state = UpdateLayoutUseCase().invoke(
            state,
            layout=LayoutType.ARC,
        )

        assert next_state.layout == LayoutType.ARC

    def test_updates_direction(self) -> None:
        """Test updating the layout direction."""
        state = ScreenState(
            direction=LayoutDirection.HORIZONTAL,
        )

        next_state = UpdateLayoutUseCase().invoke(
            state,
            direction=LayoutDirection.VERTICAL,
        )

        assert next_state.direction == LayoutDirection.VERTICAL

    def test_updates_spacing(self) -> None:
        """Test updating the spacing parameter."""
        state = ScreenState(spacing=10)

        next_state = UpdateLayoutUseCase().invoke(state, spacing=20)

        assert next_state.spacing == 20

    def test_updates_grid_columns(self) -> None:
        """Test updating grid columns with minimum validation."""
        state = ScreenState(grid_columns=3)

        next_state = UpdateLayoutUseCase().invoke(state, grid_columns=4)

        assert next_state.grid_columns == 4

    def test_clamps_grid_columns_to_minimum(self) -> None:
        """Test that grid columns are clamped to at least 1."""
        state = ScreenState(grid_columns=3)

        next_state = UpdateLayoutUseCase().invoke(state, grid_columns=0)

        assert next_state.grid_columns == 1

    def test_updates_grid_rows(self) -> None:
        """Test updating grid rows."""
        state = ScreenState(grid_rows=2)

        next_state = UpdateLayoutUseCase().invoke(state, grid_rows=3)

        assert next_state.grid_rows == 3

    def test_updates_crop_size(self) -> None:
        """Test updating crop size."""
        state = ScreenState(crop_size=512)

        next_state = UpdateLayoutUseCase().invoke(state, crop_size=1024)

        assert next_state.crop_size == 1024

    def test_clamps_crop_size_to_native_max_resolution(self) -> None:
        """Test that crop size cannot exceed the largest imported frame."""
        state = ScreenState(crop_size=512, native_max_resolution=800)

        next_state = UpdateLayoutUseCase().invoke(state, crop_size=4000)

        assert next_state.crop_size == 800

    def test_clamps_crop_size_to_minimum(self) -> None:
        """Test that crop size cannot go below the resolution floor."""
        state = ScreenState(crop_size=512)

        next_state = UpdateLayoutUseCase().invoke(state, crop_size=10)

        assert next_state.crop_size == 200

    def test_updates_threshold(self) -> None:
        """Test updating threshold."""
        state = ScreenState(threshold=128)

        next_state = UpdateLayoutUseCase().invoke(state, threshold=100)

        assert next_state.threshold == 100

    def test_updates_arc_angle(self) -> None:
        """Test updating arc angle."""
        state = ScreenState(arc_angle=90.0)

        next_state = UpdateLayoutUseCase().invoke(state, arc_angle=120.0)

        assert next_state.arc_angle == 120.0

    def test_clamps_arc_angle_to_positive_maximum(self) -> None:
        """Test that arc angle cannot exceed 180 degrees."""
        state = ScreenState(arc_angle=0.0)

        next_state = UpdateLayoutUseCase().invoke(state, arc_angle=270.0)

        assert next_state.arc_angle == 180.0

    def test_clamps_arc_angle_to_negative_minimum(self) -> None:
        """Test that arc angle cannot go below -180 degrees."""
        state = ScreenState(arc_angle=0.0)

        next_state = UpdateLayoutUseCase().invoke(state, arc_angle=-270.0)

        assert next_state.arc_angle == -180.0
