"""Unit tests for ClearImagesUseCase."""

from pathlib import Path

import pytest

from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases import ClearImagesUseCase


class TestClearImagesUseCase:
    """Test suite for ClearImagesUseCase."""

    def test_resets_gallery_and_selection(self) -> None:
        """Test that clearing images empties the gallery and clears selection."""
        state = ScreenState(
            images=(
                ImageItem(path=Path("/tmp/first.jpg")),
                ImageItem(path=Path("/tmp/second.jpg")),
            ),
            selected_index=0,
            proxy_ready=True,
        )

        next_state = ClearImagesUseCase().invoke(state)

        assert len(next_state.images) == 0
        assert next_state.selected_index is None
        assert next_state.proxy_ready is False

    def test_clears_preview_on_empty_gallery(self) -> None:
        """Test that preview is cleared when gallery becomes empty."""
        state = ScreenState(
            images=(ImageItem(path=Path("/tmp/first.jpg")),),
            selected_preview_bgr=object(),
            proxy_ready=True,
        )

        next_state = ClearImagesUseCase().invoke(state)

        assert next_state.selected_preview_bgr is None
        assert next_state.proxy_ready is False

    def test_idempotent_on_empty_gallery(self) -> None:
        """Test that clearing an empty gallery is safe."""
        state = ScreenState()

        next_state = ClearImagesUseCase().invoke(state)

        assert next_state.images == state.images
        assert next_state.selected_index is None
