"""Use case for finalizing a cancelled blocking job."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class BlockingJobCancelledUseCase:
    """Reset the screen state after a worker acknowledges cancellation."""

    def invoke(self, state: ScreenState) -> ScreenState:
        return replace(
            state,
            blocking_job=None,
            blocking_job_path=None,
            blocking_job_cancelling=False,
            import_status=JobStatus.IDLE,
            export_status=JobStatus.IDLE,
            progress=0.0,
            status_message="Cancelled.",
            error_message=None,
        )
