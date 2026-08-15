"""Use case for updating project save progress."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class SaveProjectProgressUseCase:
    """Update state while project saving is running."""

    def invoke(self, state: ScreenState, progress: float, message: str) -> ScreenState:
        return replace(
            state,
            progress=progress,
            status_message=message,
            export_status=JobStatus.RUNNING,
        )
