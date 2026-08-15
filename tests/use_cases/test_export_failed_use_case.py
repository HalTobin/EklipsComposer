"""Unit tests for ExportFailedUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus, BlockingJob
from eclipse_compositor.ui.use_cases import ExportFailedUseCase


class TestExportFailedUseCase:
    """Test suite for ExportFailedUseCase."""

    def test_sets_error_message(self) -> None:
        """Test that error message is set on export failure."""
        state = ScreenState()

        next_state = ExportFailedUseCase().invoke(state, "Write error")

        assert next_state.error_message == "Write error"
        assert next_state.status_message == "Export failed."

    def test_sets_export_status_to_idle(self) -> None:
        """Test that export status is set to idle on failure."""
        state = ScreenState(export_status=JobStatus.RUNNING)

        next_state = ExportFailedUseCase().invoke(state, "Permission denied")

        assert next_state.export_status == JobStatus.IDLE

    def test_clears_blocking_job(self) -> None:
        """Test that blocking job is cleared on failure."""
        state = ScreenState(
            blocking_job=BlockingJob.EXPORT,
            blocking_job_path="test.png",
        )

        next_state = ExportFailedUseCase().invoke(state, "Export error")

        assert next_state.blocking_job is None
        assert next_state.blocking_job_path is None
        assert next_state.blocking_job_cancelling is False
