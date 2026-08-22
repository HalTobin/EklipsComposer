"""Use case to initialize adjust circle state for a selected image."""

from __future__ import annotations
from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_state import AdjustCircleState


@dataclass(frozen=True)
class LoadAdjustCircleUseCase:
    """Prepare a new adjust-circle state when the modal opens."""

    def invoke(self, state: AdjustCircleState, path: Path, index: int, threshold: int) -> AdjustCircleState:
        return replace(
            state,
            image_index=index,
            path=path,
            threshold=threshold,
            show_circle=True,
            image_bgr=None,
            detection=None,
            error_message=None,
            is_loading=True,
            is_ready=False,
        )
