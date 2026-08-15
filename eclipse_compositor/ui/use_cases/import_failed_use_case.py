"""Use case for handling import job failure."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState, JobStatus


@dataclass(frozen=True)
class ImportFailedUseCase:
    """Update state when image import job fails."""

    def invoke(self, state: ScreenState, message: str) -> ScreenState:
        return replace(
            state,
            import_status=JobStatus.IDLE,
            error_message=message,
            status_message="Import failed.",
        )
