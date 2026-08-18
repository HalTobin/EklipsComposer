"""Use case for switching the gallery visual layout."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import GalleryViewMode, ScreenState


@dataclass(frozen=True)
class UpdateGalleryViewModeUseCase:
    """Change how the frame list is presented."""

    def invoke(self, state: ScreenState, value: GalleryViewMode) -> ScreenState:
        mode = value if isinstance(value, GalleryViewMode) else GalleryViewMode(value)
        if mode == state.gallery_view_mode:
            return state
        return replace(state, gallery_view_mode=mode)
