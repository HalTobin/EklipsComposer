"""Use case for color-grade adjustments that affect the live preview."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import (
    DEFAULT_BRIGHTNESS,
    DEFAULT_CONTRAST,
    DEFAULT_GAMMA,
    DEFAULT_SATURATION,
    DEFAULT_TEMPERATURE,
    ScreenState,
)


@dataclass(frozen=True)
class UpdateColorimetryUseCase:
    """Apply colorimetry controls while clamping them to valid ranges."""

    def invoke(
        self,
        state: ScreenState,
        *,
        contrast: float | None = None,
        saturation: float | None = None,
        brightness: float | None = None,
        gamma: float | None = None,
        temperature: float | None = None,
        reset: bool = False,
    ) -> ScreenState:
        if reset:
            return replace(
                state,
                contrast=DEFAULT_CONTRAST,
                saturation=DEFAULT_SATURATION,
                brightness=DEFAULT_BRIGHTNESS,
                gamma=DEFAULT_GAMMA,
                temperature=DEFAULT_TEMPERATURE,
            )

        next_state = state
        if contrast is not None:
            next_state = replace(next_state, contrast=max(0.5, min(2.0, float(contrast))))
        if saturation is not None:
            next_state = replace(next_state, saturation=max(0.0, min(2.0, float(saturation))))
        if brightness is not None:
            next_state = replace(next_state, brightness=max(-100.0, min(100.0, float(brightness))))
        if gamma is not None:
            next_state = replace(next_state, gamma=max(0.5, min(2.0, float(gamma))))
        if temperature is not None:
            next_state = replace(next_state, temperature=max(-100.0, min(100.0, float(temperature))))
        return next_state
