"""Unit tests for the adjust circle feature integration."""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_actions import (
    ApplyAdjustment,
    DetectCircleResult,
    UpdateAdjustCircleThreshold,
)
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_viewmodel import AdjustCircleViewModel


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_adjust_circle_viewmodel_updates_threshold() -> None:
    _get_app()
    vm = AdjustCircleViewModel()

    vm.dispatch(UpdateAdjustCircleThreshold(value=125))

    assert vm.state.threshold == 125


def test_adjust_circle_viewmodel_detect_result_sets_state() -> None:
    _get_app()
    vm = AdjustCircleViewModel()
    detection = DiscDetection(center=(50, 50), radius=32.0, area=3200.0, confidence=0.9)

    vm.dispatch(DetectCircleResult(detection=detection))

    assert vm.state.detection is detection
    assert vm.state.is_ready is True


def test_adjust_circle_viewmodel_emits_manual_detection_signal() -> None:
    _get_app()
    vm = AdjustCircleViewModel()
    detection = DiscDetection(center=(50, 50), radius=32.0, area=3200.0, confidence=0.9)
    emitted: list[tuple[int, DiscDetection]] = []
    vm.manual_detection_applied.connect(lambda index, det: emitted.append((index, det)))
    vm.dispatch(UpdateAdjustCircleThreshold(value=100))
    vm._state = vm._state.__class__(image_index=0, detection=detection, is_ready=True)

    vm.dispatch(ApplyAdjustment())

    assert emitted == [(0, detection)]
