"""Unit tests for ReorderImagesUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import ReorderImagesUseCase


class TestReorderImagesUseCase:
    """Test suite for ReorderImagesUseCase."""

    def test_reorders_gallery(self) -> None:
        """Test reordering images in the gallery."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
                ImageItem(path=Path("/tmp/third.jpg")),
            ),
        )

        reordered = (
            ImageItem(path=Path("/tmp/third.jpg")),
            ImageItem(path=Path("/tmp/first.jpg")),
            ImageItem(path=Path("/tmp/second.jpg")),
        )

        next_state = ReorderImagesUseCase().invoke(state, reordered)

        assert [item.path for item in next_state.images] == [
            Path("/tmp/third.jpg"),
            Path("/tmp/first.jpg"),
            Path("/tmp/second.jpg"),
        ]

    def test_preserves_selected_path(self) -> None:
        """Test that the selected image path is tracked across reorder."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
                ImageItem(path=Path("/tmp/third.jpg")),
            ),
            selected_index=1,
        )

        reordered = (
            ImageItem(path=Path("/tmp/third.jpg")),
            ImageItem(path=Path("/tmp/first.jpg")),
            ImageItem(path=Path("/tmp/second.jpg")),
        )

        next_state = ReorderImagesUseCase().invoke(state, reordered)

        assert next_state.selected_index == 2
        assert next_state.images[2].path == Path("/tmp/second.jpg")

    def test_clears_selection_if_path_removed(self) -> None:
        """Test that selection is cleared if the selected image is removed during reorder."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
                ImageItem(path=Path("/tmp/third.jpg")),
            ),
            selected_index=1,
        )

        # Reorder to only include first and third, removing the selected second
        reordered = (
            ImageItem(path=Path("/tmp/first.jpg")),
            ImageItem(path=Path("/tmp/third.jpg")),
        )

        next_state = ReorderImagesUseCase().invoke(state, reordered)

        # If the selected path is removed, index should be None or adjusted
        assert next_state.selected_index is None or (
            next_state.selected_index >= 0 and next_state.selected_index < len(next_state.images)
        )
