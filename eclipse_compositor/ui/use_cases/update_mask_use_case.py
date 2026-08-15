"""Use case for mask-related preview parameters."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class UpdateMaskUseCase:
    """Clamp and apply mask settings to the state."""

    def invoke(
        self,
        state: ScreenState,
        *,
        enabled: bool | None = None,
        size: float | None = None,
        feather: float | None = None,
    ) -> ScreenState:
        next_state = state
        if enabled is not None:
            next_state = replace(next_state, mask_enabled=bool(enabled))
        if size is not None:
            next_state = replace(next_state, mask_size=max(0.0, min(1.50, float(size))))
        if feather is not None:
            next_state = replace(next_state, mask_feather=max(0.0, min(0.80, float(feather))))
        return next_state
