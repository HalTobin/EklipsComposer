"""Use case for changing project gallery visibility."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class UpdateProjectGalleryHiddenUseCase:
    """Show or hide the project frame gallery."""

    def invoke(self, state: ScreenState, hidden: bool) -> ScreenState:
        if hidden == state.project_gallery_hidden:
            return state
        return replace(state, project_gallery_hidden=hidden)