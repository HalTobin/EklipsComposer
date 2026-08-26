"""Use case to initialize adjust circle state for a selected image."""

from __future__ import annotations
from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_state import AdjustCircleState


@dataclass(frozen=True)
class LoadAdjustCircleUseCase:
    """Prepare a new adjust-circle state when the modal opens."""

    def invoke(
        self,
        state: AdjustCircleState,
        path: Path,
        index: int,
        threshold: int,
        existing_detection: DiscDetection | None = None,
        existing_manual_detection: DiscDetection | None = None,
    ) -> AdjustCircleState:
        manual_center = (
            existing_manual_detection.center if existing_manual_detection else None
        )
        manual_radius = (
            existing_manual_detection.radius if existing_manual_detection else None
        )
        detection = existing_manual_detection or existing_detection
        return replace(
            state,
            image_index=index,
            path=path,
            threshold=threshold,
            show_circle=True,
            image_bgr=None,
            detection=detection,
            manual_center=manual_center,
            manual_radius=manual_radius,
            error_message=None,
            is_loading=True,
            is_ready=False,
        )
