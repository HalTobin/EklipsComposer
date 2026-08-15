"""Unit tests for OpenProjectProgressUseCase."""

from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.use_cases import OpenProjectProgressUseCase


class TestOpenProjectProgressUseCase:
    """Test suite for OpenProjectProgressUseCase."""

    def test_updates_progress_and_import_status(self) -> None:
        state = ScreenState()

        next_state = OpenProjectProgressUseCase().invoke(state, 0.5, "Opening project")

        assert next_state.progress == 0.5
        assert next_state.status_message == "Opening project"
        assert next_state.import_status == JobStatus.RUNNING
