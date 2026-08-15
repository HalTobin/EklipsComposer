"""Unit tests for ImportProgressUseCase."""

from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.use_cases import ImportProgressUseCase


class TestImportProgressUseCase:
    """Test suite for ImportProgressUseCase."""

    def test_updates_progress_and_import_status(self) -> None:
        state = ScreenState()

        next_state = ImportProgressUseCase().invoke(state, 0.4, "Importing frame")

        assert next_state.progress == 0.4
        assert next_state.status_message == "Importing frame"
        assert next_state.import_status == JobStatus.RUNNING
