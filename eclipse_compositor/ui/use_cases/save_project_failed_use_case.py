"""Use case for handling save project job failure."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState, JobStatus


@dataclass(frozen=True)
class SaveProjectFailedUseCase:
    """Update state when save project job fails."""

    def invoke(self, state: ScreenState, message: str) -> ScreenState:
        return replace(
            state,
            export_status=JobStatus.IDLE,
            error_message=message,
            status_message="Save failed.",
            blocking_job=None,
            blocking_job_path=None,
            blocking_job_cancelling=False,
        )
