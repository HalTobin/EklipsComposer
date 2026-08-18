"""Use case for filtering the gallery to favorites and the current selection."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class UpdateGalleryShowOnlyFavoritesUseCase:
    """Toggle the gallery favorite-only filter."""

    def invoke(self, state: ScreenState, value: bool) -> ScreenState:
        show_only = bool(value)
        if show_only == state.gallery_show_only_favorites:
            return state
        return replace(state, gallery_show_only_favorites=show_only)
