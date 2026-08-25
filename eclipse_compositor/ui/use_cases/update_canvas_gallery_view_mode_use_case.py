"""Use case for switching the canvas gallery visual layout."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import GalleryViewMode, ScreenState


@dataclass(frozen=True)
class UpdateCanvasGalleryViewModeUseCase:
    """Change how the canvas frame list is presented."""

    def invoke(self, state: ScreenState, value: GalleryViewMode) -> ScreenState:
        mode = value if isinstance(value, GalleryViewMode) else GalleryViewMode(value)
        if mode is GalleryViewMode.ICON:
            mode = GalleryViewMode.LIST_SIMPLE
        if mode == state.canvas_gallery_view_mode:
            return state
        return replace(state, canvas_gallery_view_mode=mode)
