"""Use case to apply the adjusted detection result back to the main gallery state."""

from __future__ import annotations
from dataclasses import dataclass, replace

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.state import AdjustCircleState
from eclipse_compositor.ui.state import ImageItem


@dataclass(frozen=True)
class ApplyAdjustCircleUseCase:
    """Attach a manual detection override to the selected gallery frame."""

    def invoke(
        self,
        state: AdjustCircleState,
        index: int,
        detection: DiscDetection,
    ) -> AdjustCircleState:
        if state.image_index != index:
            return state
        return replace(state)
