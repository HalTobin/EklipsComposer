"""Unit tests for the adjust circle feature integration."""

from pathlib import Path

import numpy as np
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QApplication

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_actions import (
    ApplyAdjustment,
    DetectCircleResult,
    ManualAdjustCircle,
    OpenAdjustCircle,
    ToggleCircleVisibility,
    UpdateAdjustCircleThreshold,
)
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_view import AdjustCircleView
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_viewmodel import AdjustCircleViewModel
from eclipse_compositor.ui.feature.adjust_circle.circle_editor import CircleEditor


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


def test_adjust_circle_viewmodel_manual_override_applied() -> None:
    _get_app()
    vm = AdjustCircleViewModel()
    emitted: list[tuple[int, DiscDetection]] = []
    vm.manual_detection_applied.connect(lambda index, det: emitted.append((index, det)))

    vm._state = vm._state.__class__(image_index=2, is_ready=True)
    vm.dispatch(ManualAdjustCircle(center=(150, 200), radius=45.0))

    assert vm.state.manual_center == (150, 200)
    assert vm.state.manual_radius == 45.0

    vm.dispatch(ApplyAdjustment())

    assert len(emitted) == 1
    idx, det = emitted[0]
    assert idx == 2
    assert det.center == (150, 200)
    assert det.radius == 45.0


def test_open_adjust_circle_preserves_existing_manual_detection() -> None:
    _get_app()
    vm = AdjustCircleViewModel()
    existing_manual = DiscDetection(center=(120, 180), radius=40.0, area=5026.5, confidence=1.0)

    vm.dispatch(
        OpenAdjustCircle(
            index=1,
            path=Path("/tmp/test.jpg"),
            threshold=180,
            existing_manual_detection=existing_manual,
        )
    )

    assert vm.state.image_index == 1
    assert vm.state.manual_center == (120, 180)
    assert vm.state.manual_radius == 40.0
    assert vm.state.detection == existing_manual


def test_adjust_circle_view_apply_closes_dialog() -> None:
    _get_app()
    vm = AdjustCircleViewModel()
    vm._state = vm._state.__class__(image_index=0, is_ready=True)

    view = AdjustCircleView(vm, vm.state)
    emitted: list[tuple[int, DiscDetection]] = []
    vm.manual_detection_applied.connect(lambda idx, det: emitted.append((idx, det)))

    # Call _on_apply directly
    view._on_apply()

    assert view.result() == 1  # Accepted (QDialog.DialogCode.Accepted)


def test_adjust_circle_viewmodel_toggles_circle_visibility() -> None:
    _get_app()
    vm = AdjustCircleViewModel()
    assert vm.state.show_circle is True

    vm.dispatch(ToggleCircleVisibility(visible=False))

    assert vm.state.show_circle is False


def test_circle_editor_coordinate_transforms() -> None:
    _get_app()
    editor = CircleEditor()
    editor.resize(400, 300)

    qimg = QImage(800, 600, QImage.Format.Format_RGB32)
    pix = QPixmap.fromImage(qimg)
    editor.setImage(pix)

    params = editor._get_transform_params()
    assert params is not None
    scale, offset_x, offset_y = params
    assert scale == 0.5
    assert offset_x == 0.0
    assert offset_y == 0.0

    widget_data = editor._image_to_widget(200.0, 100.0, 50.0)
    assert widget_data is not None
    wpt, wradius = widget_data
    assert wpt.x() == 100.0
    assert wpt.y() == 50.0
    assert wradius == 25.0
