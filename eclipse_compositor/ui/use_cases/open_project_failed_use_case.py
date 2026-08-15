"""Use case for handling open project job failure."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState, JobStatus


@dataclass(frozen=True)
class OpenProjectFailedUseCase:
    """Update state when open project job fails."""

    def invoke(self, state: ScreenState, message: str) -> ScreenState:
        return replace(
            state,
            import_status=JobStatus.IDLE,
            error_message=message,
            status_message="Open failed.",
            blocking_job=None,
            blocking_job_path=None,
            blocking_job_cancelling=False,
        )
