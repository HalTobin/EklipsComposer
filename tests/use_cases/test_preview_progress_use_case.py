"""Unit tests for PreviewProgressUseCase."""

from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.use_cases import PreviewProgressUseCase


class TestPreviewProgressUseCase:
    """Test suite for PreviewProgressUseCase."""

    def test_updates_progress_and_preview_status(self) -> None:
        state = ScreenState()

        next_state = PreviewProgressUseCase().invoke(state, 0.6, "Rendering preview")

        assert next_state.progress == 0.6
        assert next_state.status_message == "Rendering preview"
        assert next_state.preview_status == JobStatus.RUNNING
