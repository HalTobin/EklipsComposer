"""Use case for preparing a project save job."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class SaveProjectUseCase:
    """Prepare the state for saving the current project archive."""

    def invoke(self, state: ScreenState, output_path: Path) -> ScreenState:
        if not state.images:
            return state

        return replace(
            state,
            export_status=JobStatus.RUNNING,
            progress=0.0,
            status_message="Saving project…",
            error_message=None,
            blocking_job_path=output_path,
        )
