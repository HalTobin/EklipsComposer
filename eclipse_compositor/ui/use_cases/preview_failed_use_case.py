"""Use case for handling preview render failure."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState, JobStatus


@dataclass(frozen=True)
class PreviewFailedUseCase:
    """Update state when preview render job fails."""

    def invoke(self, state: ScreenState, message: str) -> ScreenState:
        return replace(
            state,
            preview_status=JobStatus.IDLE,
            error_message=message,
            status_message="Preview failed.",
        )
