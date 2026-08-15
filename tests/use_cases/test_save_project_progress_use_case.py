"""Unit tests for SaveProjectProgressUseCase."""

from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.use_cases import SaveProjectProgressUseCase


class TestSaveProjectProgressUseCase:
    """Test suite for SaveProjectProgressUseCase."""

    def test_updates_progress_and_export_status(self) -> None:
        state = ScreenState()

        next_state = SaveProjectProgressUseCase().invoke(state, 0.7, "Saving project")

        assert next_state.progress == 0.7
        assert next_state.status_message == "Saving project"
        assert next_state.export_status == JobStatus.RUNNING
