"""Use case for checking or unchecking every gallery frame at once."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class SetAllEnabledUseCase:
    """Enable or disable all frames in the composite."""

    def invoke(self, state: ScreenState, enabled: bool) -> ScreenState:
        if not state.images:
            return state

        images = tuple(replace(item, enabled=enabled) for item in state.images)
        if images == state.images:
            return state
        return replace(state, images=images)
