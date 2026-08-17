"""Use case for layout-scale state updates that trigger preview recalculation."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.ui.state import MIN_RESOLUTION, ScreenState


@dataclass(frozen=True)
class UpdateLayoutUseCase:
    """Apply a layout-related mutation to the state."""

    def invoke(self, state: ScreenState, *, crop_size: int | None = None, spacing: float | None = None, layout: LayoutType | None = None, arc_angle: float | None = None, direction: LayoutDirection | None = None, threshold: int | None = None, grid_columns: int | None = None, grid_rows: int | None = None) -> ScreenState:
        next_state = state

        if crop_size is not None:
            capped = max(MIN_RESOLUTION, min(int(crop_size), state.native_max_resolution))
            next_state = replace(next_state, crop_size=capped)
        if spacing is not None:
            next_state = replace(next_state, spacing=spacing)
        if layout is not None:
            next_state = replace(next_state, layout=layout)
        if arc_angle is not None:
            next_state = replace(next_state, arc_angle=max(-180.0, min(180.0, float(arc_angle))))
        if direction is not None:
            next_state = replace(next_state, direction=direction)
        if threshold is not None:
            next_state = replace(next_state, threshold=threshold)
        if grid_columns is not None:
            next_state = replace(next_state, grid_columns=max(1, int(grid_columns)))
        if grid_rows is not None:
            next_state = replace(next_state, grid_rows=max(1, int(grid_rows)))

        return next_state
