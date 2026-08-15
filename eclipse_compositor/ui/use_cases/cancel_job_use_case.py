"""Use case for cancelling the current blocking job."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class CancelJobUseCase:
    """Prepare the state to reflect a cooperative cancellation request."""

    def invoke(self, state: ScreenState) -> ScreenState:
        if state.blocking_job is None:
            return state
        return replace(
            state,
            blocking_job_cancelling=True,
            status_message="Cancelling…",
        )
