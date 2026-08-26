"""Use case to apply the adjusted detection result back to the main gallery state."""

from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_state import AdjustCircleState


@dataclass(frozen=True)
class ApplyAdjustCircleUseCase:
    """Attach a manual detection override to the selected gallery frame."""

    def invoke(
        self,
        state: AdjustCircleState,
        index: int,
        detection: DiscDetection | None = None,
    ) -> AdjustCircleState:
        if state.image_index != index:
            return state

        effective_detection: DiscDetection | None = None
        if state.manual_center is not None and state.manual_radius is not None:
            center = state.manual_center
            radius = float(state.manual_radius)
            area = (
                state.detection.area
                if state.detection is not None
                else float(np.pi * radius * radius)
            )
            confidence = (
                state.detection.confidence
                if state.detection is not None
                else 1.0
            )
            effective_detection = DiscDetection(
                center=center,
                radius=radius,
                area=area,
                confidence=confidence,
            )
        elif detection is not None:
            effective_detection = detection
        elif state.detection is not None:
            effective_detection = state.detection

        return replace(state, detection=effective_detection)
