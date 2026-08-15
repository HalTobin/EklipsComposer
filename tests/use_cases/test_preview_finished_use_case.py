"""Unit tests for PreviewFinishedUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import PreviewFinishedUseCase


class TestPreviewFinishedUseCase:
    """Test suite for PreviewFinishedUseCase."""

    def test_stores_preview_image(self) -> None:
        """Test that preview image is stored."""
        state = ScreenState()
        preview_obj = object()

        next_state = PreviewFinishedUseCase().invoke(state, preview_obj, 10)

        assert next_state.preview_bgr is preview_obj

    def test_updates_preview_generation(self) -> None:
        """Test that preview generation is updated."""
        state = ScreenState()

        next_state = PreviewFinishedUseCase().invoke(state, object(), 11)

        assert next_state._preview_generation == 11

    def test_clears_preview_status(self) -> None:
        """Test that preview status is cleared after successful render."""
        state = ScreenState(preview_status=JobStatus.RUNNING)

        next_state = PreviewFinishedUseCase().invoke(state, object(), 5)

        assert next_state.preview_status is None
