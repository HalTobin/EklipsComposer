"""Use case for zoom updates on the preview viewport."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class UpdateZoomUseCase:
    """Clamp viewport zoom to a safe range."""

    def invoke(self, state: ScreenState, value: float) -> ScreenState:
        zoom = max(0.01, min(8.0, float(value)))
        if abs(zoom - state.zoom) < 1e-6:
            return state
        return replace(state, zoom=zoom)
