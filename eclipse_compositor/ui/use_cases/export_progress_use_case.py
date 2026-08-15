"""Use case for updating composite export progress."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class ExportProgressUseCase:
    """Update state while composite export is running."""

    def invoke(self, state: ScreenState, progress: float, message: str) -> ScreenState:
        return replace(
            state,
            progress=progress,
            status_message=message,
            export_status=JobStatus.RUNNING,
        )
