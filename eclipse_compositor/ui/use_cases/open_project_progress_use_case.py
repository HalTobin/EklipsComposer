"""Use case for updating project open progress."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class OpenProjectProgressUseCase:
    """Update state while project opening is running."""

    def invoke(self, state: ScreenState, progress: float, message: str) -> ScreenState:
        return replace(
            state,
            progress=progress,
            status_message=message,
            import_status=JobStatus.RUNNING,
        )
