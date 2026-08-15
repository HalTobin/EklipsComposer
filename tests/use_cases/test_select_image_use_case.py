"""Unit tests for SelectImageUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import SelectImageUseCase


class TestSelectImageUseCase:
    """Test suite for SelectImageUseCase."""

    def test_selects_valid_index(self) -> None:
        """Test selecting an image by valid index."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
        )

        next_state = SelectImageUseCase().invoke(state, 1)

        assert next_state.selected_index == 1

    def test_clears_selection_with_none(self) -> None:
        """Test clearing selection with None."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/first.jpg")),),
            selected_index=0,
        )

        next_state = SelectImageUseCase().invoke(state, None)

        assert next_state.selected_index is None

    def test_bounds_check_out_of_range(self) -> None:
        """Test that out-of-range index is clamped to None."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
        )

        next_state = SelectImageUseCase().invoke(state, 5)

        assert next_state.selected_index is None

    def test_bounds_check_negative_index(self) -> None:
        """Test that negative index is clamped to None."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/first.jpg")),),
        )

        next_state = SelectImageUseCase().invoke(state, -1)

        assert next_state.selected_index is None
