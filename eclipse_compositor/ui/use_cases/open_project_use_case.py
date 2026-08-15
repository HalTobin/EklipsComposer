"""Use case for preparing an opened project import job."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class OpenProjectUseCase:
    """Prepare the state for opening a saved project archive."""

    def invoke(self, state: ScreenState, archive_path: Path) -> ScreenState:
        return replace(
            state,
            import_status=JobStatus.RUNNING,
            progress=0.0,
            status_message="Opening project…",
            error_message=None,
            blocking_job_path=archive_path,
        )
