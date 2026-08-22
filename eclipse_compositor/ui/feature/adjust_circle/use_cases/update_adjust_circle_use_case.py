"""Use case to mutate adjust circle modal state."""

from __future__ import annotations
from dataclasses import dataclass, replace

from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_state import AdjustCircleState


@dataclass(frozen=True)
class UpdateAdjustCircleUseCase:
    """Apply one or more field updates to the adjust-circle state."""

    def invoke(
        self,
        state: AdjustCircleState,
        *,
        threshold: int | None = None,
        show_circle: bool | None = None,
        image_bgr: object | None = None,
        detection: object | None = None,
        error_message: str | None = None,
        is_loading: bool | None = None,
        is_ready: bool | None = None,
    ) -> AdjustCircleState:
        next_state = state
        if threshold is not None:
            next_state = replace(next_state, threshold=int(threshold))
        if show_circle is not None:
            next_state = replace(next_state, show_circle=show_circle)
        if image_bgr is not None:
            next_state = replace(next_state, image_bgr=image_bgr)
        if detection is not None:
            next_state = replace(next_state, detection=detection)
        if error_message is not None:
            next_state = replace(next_state, error_message=error_message)
        if is_loading is not None:
            next_state = replace(next_state, is_loading=is_loading)
        if is_ready is not None:
            next_state = replace(next_state, is_ready=is_ready)
        return next_state
