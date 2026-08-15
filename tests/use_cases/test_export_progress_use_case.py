"""Unit tests for ExportProgressUseCase."""

from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.use_cases import ExportProgressUseCase


class TestExportProgressUseCase:
    """Test suite for ExportProgressUseCase."""

    def test_updates_progress_and_export_status(self) -> None:
        state = ScreenState()

        next_state = ExportProgressUseCase().invoke(state, 0.8, "Exporting composite")

        assert next_state.progress == 0.8
        assert next_state.status_message == "Exporting composite"
        assert next_state.export_status == JobStatus.RUNNING
