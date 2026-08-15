"""Unit tests for SaveProjectFailedUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus, BlockingJob
from eclipse_compositor.ui.use_cases import SaveProjectFailedUseCase


class TestSaveProjectFailedUseCase:
    """Test suite for SaveProjectFailedUseCase."""

    def test_sets_error_message(self) -> None:
        """Test that error message is set on save failure."""
        state = ScreenState()

        next_state = SaveProjectFailedUseCase().invoke(state, "Disk full")

        assert next_state.error_message == "Disk full"
        assert next_state.status_message == "Save failed."

    def test_sets_export_status_to_idle(self) -> None:
        """Test that export status is set to idle on failure."""
        state = ScreenState(export_status=JobStatus.RUNNING)

        next_state = SaveProjectFailedUseCase().invoke(state, "Write error")

        assert next_state.export_status == JobStatus.IDLE

    def test_clears_blocking_job(self) -> None:
        """Test that blocking job is cleared on failure."""
        state = ScreenState(
            blocking_job=BlockingJob.SAVE,
            blocking_job_path="project.vlt",
        )

        next_state = SaveProjectFailedUseCase().invoke(state, "Save error")

        assert next_state.blocking_job is None
        assert next_state.blocking_job_path is None
        assert next_state.blocking_job_cancelling is False
