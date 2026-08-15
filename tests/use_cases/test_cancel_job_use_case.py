"""Unit tests for CancelJobUseCase."""

import pytest

from eclipse_compositor.ui.state import ScreenState, BlockingJob
from eclipse_compositor.ui.use_cases import CancelJobUseCase


class TestCancelJobUseCase:
    """Test suite for CancelJobUseCase."""

    def test_sets_cancelling_flag(self) -> None:
        """Test that cancelling flag is set during cancellation."""
        state = ScreenState(
            blocking_job=BlockingJob.EXPORT,
            blocking_job_cancelling=False,
        )

        next_state = CancelJobUseCase().invoke(state)

        assert next_state.blocking_job_cancelling is True
        assert next_state.blocking_job == BlockingJob.EXPORT
        assert "cancel" in next_state.status_message.lower()

    def test_updates_status_message(self) -> None:
        """Test that status message is updated during cancellation."""
        state = ScreenState(blocking_job=BlockingJob.EXPORT)

        next_state = CancelJobUseCase().invoke(state)

        assert next_state.status_message == "Cancelling…"

    def test_idempotent_when_no_job_running(self) -> None:
        """Test that cancelling when no job is running is safe."""
        state = ScreenState(blocking_job=None)

        next_state = CancelJobUseCase().invoke(state)

        assert next_state.blocking_job is None
