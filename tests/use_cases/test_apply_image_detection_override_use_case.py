"""Unit tests for ApplyImageDetectionOverrideUseCase."""

from pathlib import Path

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.state import ImageItem, ScreenState
from eclipse_compositor.ui.use_cases.apply_image_detection_override_use_case import (
    ApplyImageDetectionOverrideUseCase,
)


class TestApplyImageDetectionOverrideUseCase:
    def test_attaches_manual_detection_to_image(self) -> None:
        image = ImageItem(path=Path("/tmp/frame.jpg"), enabled=True)
        state = ScreenState(images=(image,))
        detection = DiscDetection(center=(10, 10), radius=20.0, area=314.0, confidence=0.9)

        next_state = ApplyImageDetectionOverrideUseCase().invoke(
            state,
            index=0,
            detection=detection,
        )

        assert next_state.images[0].manual_detection is detection
        assert next_state.images[0].detection_ok is True

    def test_returns_same_state_for_invalid_index(self) -> None:
        state = ScreenState(images=())
        detection = DiscDetection(center=(10, 10), radius=20.0, area=314.0, confidence=0.9)

        next_state = ApplyImageDetectionOverrideUseCase().invoke(
            state,
            index=1,
            detection=detection,
        )

        assert next_state is state
