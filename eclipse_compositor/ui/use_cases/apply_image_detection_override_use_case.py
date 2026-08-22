"""Use case for applying a manual detection override to a selected frame."""

from __future__ import annotations
from dataclasses import dataclass, replace

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.state import ImageItem, ScreenState


@dataclass(frozen=True)
class ApplyImageDetectionOverrideUseCase:
    """Apply a manual detection override to one image in the state."""

    def invoke(
        self,
        state: ScreenState,
        index: int,
        detection: DiscDetection,
    ) -> ScreenState:
        if not (0 <= index < len(state.images)):
            return state

        images = list(state.images)
        item = images[index]
        images[index] = replace(
            item,
            manual_detection=detection,
            detection_ok=True,
        )
        return replace(state, images=tuple(images))
