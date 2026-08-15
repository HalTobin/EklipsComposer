"""Use case for updating preview progress."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import JobStatus, ScreenState


@dataclass(frozen=True)
class PreviewProgressUseCase:
    """Update state while preview rendering is running."""

    def invoke(self, state: ScreenState, progress: float, message: str) -> ScreenState:
        return replace(
            state,
            progress=progress,
            status_message=message,
            preview_status=JobStatus.RUNNING,
        )
