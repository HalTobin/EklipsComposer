"""Use case for applying the results of a successful project open."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class ProjectOpenedUseCase:
    """Finalize the open-project state after the project archive is loaded."""

    def invoke(self, state: ScreenState, project_path: Path) -> ScreenState:
        return replace(
            state,
            last_project_path=project_path,
            import_status=None,
            progress=1.0,
            status_message=f"Opened {project_path.name}.",
            error_message=None,
        )
