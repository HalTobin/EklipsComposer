"""Use case for canvas margin state adjustments."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import MAX_MARGIN, MIN_MARGIN, ScreenState


@dataclass(frozen=True)
class UpdateCanvasUseCase:
    """Clamp and apply margin settings for the composited canvas."""

    def invoke(
        self,
        state: ScreenState,
        *,
        margin_linked: bool | None = None,
        margin_x: int | None = None,
        margin_y: int | None = None,
        margin_global: int | None = None,
    ) -> ScreenState:
        next_state = state

        if margin_linked is not None:
            next_state = replace(next_state, margin_linked=bool(margin_linked))
        if margin_global is not None:
            margin = max(MIN_MARGIN, min(MAX_MARGIN, int(margin_global)))
            next_state = replace(
                next_state,
                margin_linked=True,
                margin_x=margin,
                margin_y=margin,
            )
        if margin_x is not None:
            next_state = replace(
                next_state,
                margin_x=max(MIN_MARGIN, min(MAX_MARGIN, int(margin_x))),
            )
        if margin_y is not None:
            next_state = replace(
                next_state,
                margin_y=max(MIN_MARGIN, min(MAX_MARGIN, int(margin_y))),
            )

        return next_state
