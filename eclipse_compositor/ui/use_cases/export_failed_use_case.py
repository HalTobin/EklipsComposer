"""Use case for handling export job failure."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState, JobStatus


@dataclass(frozen=True)
class ExportFailedUseCase:
    """Update state when export job fails."""

    def invoke(self, state: ScreenState, message: str) -> ScreenState:
        return replace(
            state,
            export_status=JobStatus.IDLE,
            error_message=message,
            status_message="Export failed.",
            blocking_job=None,
            blocking_job_path=None,
            blocking_job_cancelling=False,
        )
