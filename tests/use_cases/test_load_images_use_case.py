"""Unit tests for LoadImagesUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import LoadImagesUseCase


class TestLoadImagesUseCase:
    """Test suite for LoadImagesUseCase."""

    def test_appends_unique_items(self) -> None:
        """Test that new images are appended and duplicates are skipped."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/first.jpg")),),
        )

        imported = (
            ImageItem(path=Path("/tmp/second.jpg")),
            ImageItem(path=Path("/tmp/first.jpg")),
        )

        next_state = LoadImagesUseCase().invoke(state, imported)

        assert len(next_state.images) == 2
        assert [item.path for item in next_state.images] == [
            Path("/tmp/first.jpg"),
            Path("/tmp/second.jpg"),
        ]

    def test_preserves_selected_index(self) -> None:
        """Test that selection is preserved when loading new images."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/first.jpg")),),
            selected_index=0,
        )

        imported = (ImageItem(path=Path("/tmp/second.jpg")),)

        next_state = LoadImagesUseCase().invoke(state, imported)

        assert next_state.selected_index == 0

    def test_loads_to_empty_gallery(self) -> None:
        """Test loading images to an empty gallery."""
        state = ScreenState()

        imported = (
            ImageItem(path=Path("/tmp/a.jpg")),
            ImageItem(path=Path("/tmp/b.jpg")),
        )

        next_state = LoadImagesUseCase().invoke(state, imported)

        assert len(next_state.images) == 2
        assert [item.path for item in next_state.images] == [
            Path("/tmp/a.jpg"),
            Path("/tmp/b.jpg"),
        ]

    def test_handles_empty_import(self) -> None:
        """Test loading with no images."""
        state = ScreenState(images=(ImageItem(path=Path("/tmp/first.jpg")),))

        next_state = LoadImagesUseCase().invoke(state, ())

        assert next_state.images == state.images
