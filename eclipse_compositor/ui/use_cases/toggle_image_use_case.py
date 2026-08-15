"""Use case for toggling the enabled state of a gallery item."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class ToggleImageUseCase:
    """Enable or disable a gallery frame without mutating the whole model."""

    def invoke(self, state: ScreenState, index: int, enabled: bool) -> ScreenState:
        if not (0 <= index < len(state.images)):
            return state

        images = list(state.images)
        images[index] = replace(images[index], enabled=enabled)
        return replace(state, images=tuple(images))
