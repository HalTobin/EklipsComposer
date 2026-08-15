"""Use case for applying the result of a successful project save."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class ProjectSavedUseCase:
    """Finalize the save state after a successful project archive write."""

    def invoke(self, state: ScreenState, output_path: Path) -> ScreenState:
        return replace(
            state,
            last_project_path=output_path,
            export_status=None,
            progress=1.0,
            status_message=f"Saved project to {output_path}.",
            error_message=None,
        )
