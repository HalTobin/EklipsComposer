"""Unit tests for RemoveImageUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import RemoveImageUseCase


class TestRemoveImageUseCase:
    """Test suite for RemoveImageUseCase."""

    def test_removes_single_image(self) -> None:
        """Test removing a single image from the gallery."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
                ImageItem(path=Path("/tmp/third.jpg")),
            ),
        )

        next_state = RemoveImageUseCase().invoke(state, (1,))

        assert len(next_state.images) == 2
        assert [item.path for item in next_state.images] == [
            Path("/tmp/first.jpg"),
            Path("/tmp/third.jpg"),
        ]

    def test_removes_multiple_images(self) -> None:
        """Test removing multiple images at once."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
                ImageItem(path=Path("/tmp/third.jpg")),
            ),
        )

        next_state = RemoveImageUseCase().invoke(state, (0, 2))

        assert len(next_state.images) == 1
        assert next_state.images[0].path == Path("/tmp/second.jpg")

    def test_keeps_selection_by_path(self) -> None:
        """Test that selection follows the selected item by path."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
                ImageItem(path=Path("/tmp/third.jpg")),
            ),
            selected_index=2,
        )

        next_state = RemoveImageUseCase().invoke(state, (1,))

        # Second image removed, third becomes index 1
        assert next_state.selected_index == 1
        assert next_state.images[1].path == Path("/tmp/third.jpg")

    def test_clears_selection_when_all_removed(self) -> None:
        """Test that selection is cleared when all images are removed."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
            selected_index=0,
        )

        next_state = RemoveImageUseCase().invoke(state, (0, 1))

        assert next_state.selected_index is None
        assert len(next_state.images) == 0
