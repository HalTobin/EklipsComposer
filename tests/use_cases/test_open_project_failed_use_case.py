"""Unit tests for OpenProjectFailedUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, JobStatus, BlockingJob
from eclipse_compositor.ui.use_cases import OpenProjectFailedUseCase


class TestOpenProjectFailedUseCase:
    """Test suite for OpenProjectFailedUseCase."""

    def test_sets_error_message(self) -> None:
        """Test that error message is set on open failure."""
        state = ScreenState()

        next_state = OpenProjectFailedUseCase().invoke(state, "File corrupted")

        assert next_state.error_message == "File corrupted"
        assert next_state.status_message == "Open failed."

    def test_sets_import_status_to_idle(self) -> None:
        """Test that import status is set to idle on failure."""
        state = ScreenState(import_status=JobStatus.RUNNING)

        next_state = OpenProjectFailedUseCase().invoke(state, "Read error")

        assert next_state.import_status == JobStatus.IDLE

    def test_clears_blocking_job(self) -> None:
        """Test that blocking job is cleared on failure."""
        state = ScreenState(
            blocking_job=BlockingJob.OPEN,
            blocking_job_path="project.vlt",
        )

        next_state = OpenProjectFailedUseCase().invoke(state, "Open error")

        assert next_state.blocking_job is None
        assert next_state.blocking_job_path is None
        assert next_state.blocking_job_cancelling is False
