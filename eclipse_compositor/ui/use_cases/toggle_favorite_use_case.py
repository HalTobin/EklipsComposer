"""Use case for toggling the favorite flag of a gallery frame."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class ToggleFavoriteUseCase:
    """Mark or unmark a frame as favorite without mutating the whole model."""

    def invoke(self, state: ScreenState, index: int, favorite: bool) -> ScreenState:
        if not (0 <= index < len(state.images)):
            return state

        images = list(state.images)
        images[index] = replace(images[index], favorite=favorite)
        return replace(state, images=tuple(images))
