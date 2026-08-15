"""Unit tests for PreviewFailedUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus
from eclipse_compositor.ui.use_cases import PreviewFailedUseCase


class TestPreviewFailedUseCase:
    """Test suite for PreviewFailedUseCase."""

    def test_sets_error_message(self) -> None:
        """Test that error message is set on preview failure."""
        state = ScreenState()

        next_state = PreviewFailedUseCase().invoke(state, "Detection failed")

        assert next_state.error_message == "Detection failed"
        assert next_state.status_message == "Preview failed."

    def test_sets_preview_status_to_idle(self) -> None:
        """Test that preview status is set to idle on failure."""
        state = ScreenState(preview_status=JobStatus.RUNNING)

        next_state = PreviewFailedUseCase().invoke(state, "Render error")

        assert next_state.preview_status == JobStatus.IDLE

    def test_clears_previous_error(self) -> None:
        """Test that new error overwrites previous one."""
        state = ScreenState(error_message="Old error")

        next_state = PreviewFailedUseCase().invoke(state, "New error")

        assert next_state.error_message == "New error"
