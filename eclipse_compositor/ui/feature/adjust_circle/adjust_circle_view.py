"""Adjust circle modal UI."""

from __future__ import annotations

import numpy as np
from dataclasses import replace

from PySide6.QtCore import Qt, QSize, Signal, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_actions import (
    ApplyAdjustment,
    AutoDetect,
    OpenAdjustCircle,
    ToggleCircleVisibility,
    UpdateAdjustCircleThreshold,
)
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_state import AdjustCircleState
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_viewmodel import AdjustCircleViewModel
from eclipse_compositor.ui.theme import ActionButton, CaptionLabel, FieldLabel, IntSliderField
from PySide6.QtWidgets import QGroupBox, QSpinBox
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage


class AdjustCircleView(QDialog):
    def __init__(self, view_model: AdjustCircleViewModel, state: AdjustCircleState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Adjust circle detection")
        self.setModal(True)
        # Set default dialog size (avoids fullscreen)
        self.setFixedSize(800, 600)
        self.view_model = view_model
        self.view_model.state_changed.connect(self.render)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = CaptionLabel("Adjust detected disc center")
        root.addWidget(header)

        # Threshold and auto-detect controls
        controls = QHBoxLayout()
        self.threshold_field = IntSliderField("Threshold", 20, 250)
        self.threshold_field.valueChanged.connect(self._on_threshold_changed)
        controls.addWidget(self.threshold_field, stretch=1)

        self.auto_btn = ActionButton("Auto detect", variant="primary")
        self.auto_btn.clicked.connect(lambda: self.view_model.dispatch(AutoDetect()))
        controls.addWidget(self.auto_btn)
        root.addLayout(controls)

        # Manual adjustment controls (spin boxes)
        manual_group = QGroupBox("Manual Adjustment")
        manual_layout = QHBoxLayout()
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 10000)
        self.spin_x.setPrefix("X: ")
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 10000)
        self.spin_y.setPrefix("Y: ")
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(1, 10000)
        self.spin_radius.setPrefix("R: ")
        manual_layout.addWidget(self.spin_x)
        manual_layout.addWidget(self.spin_y)
        manual_layout.addWidget(self.spin_radius)
        manual_group.setLayout(manual_layout)
        root.addWidget(manual_group)

        # Connect spin box changes to dispatch ManualAdjustCircle
        self.spin_x.valueChanged.connect(self._on_manual_changed)
        self.spin_y.valueChanged.connect(self._on_manual_changed)
        self.spin_radius.valueChanged.connect(self._on_manual_changed)

        # Interactive preview widget
        from .circle_editor import CircleEditor
        self.circle_editor = CircleEditor()
        self.circle_editor.setFixedSize(QSize(680, 420))
        self.circle_editor.setStyleSheet("border: 1px solid #444; background: #111;")
        self.circle_editor.geometryChanged.connect(
            lambda cx, cy, r: self.view_model.dispatch(
                ManualAdjustCircle(center=(int(cx), int(cy)), radius=float(r))
            )
        )
        root.addWidget(self.circle_editor)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self.status_label)

        self.circle_toggle = QPushButton("Hide circle")
        self.circle_toggle.clicked.connect(self._toggle_circle)
        root.addWidget(self.circle_toggle)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Close")
        buttons.accepted.connect(lambda: self.view_model.dispatch(ApplyAdjustment()))
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.render(state)

    def _on_threshold_changed(self, value: int) -> None:
        self.view_model.dispatch(UpdateAdjustCircleThreshold(value=value))

    def _on_manual_changed(self, _: int) -> None:
        # Dispatch current spin box values as manual adjustment
        center = (self.spin_x.value(), self.spin_y.value())
        radius = self.spin_radius.value()
        self.view_model.dispatch(ManualAdjustCircle(center=center, radius=radius))

    def _toggle_circle(self) -> None:
        state = self.view_model.state
        self.view_model.dispatch(ToggleCircleVisibility(visible=not state.show_circle))

    def render(self, state: AdjustCircleState) -> None:
        # Update controls to reflect state
        self.threshold_field.setValue(state.threshold)
        self.circle_toggle.setText("Hide circle" if state.show_circle else "Show circle")
        if state.error_message:
            self.status_label.setText(f"Error: {state.error_message}")
        elif not state.is_ready:
            self.status_label.setText("Loading image and detection…")
        elif state.detection is None:
            self.status_label.setText("No disc was found. Try adjusting the threshold or run auto detection.")
        else:
            self.status_label.setText(
                f"Detected center at {state.detection.center}, radius {state.detection.radius:.1f}."
            )

        if state.image_bgr is None:
            self.circle_editor.setImage(QPixmap())
            return
        image = state.image_bgr
        if isinstance(image, np.ndarray):
            qimg = bgr_to_qimage(image)
            pix = QPixmap.fromImage(qimg)
            if not pix.isNull():
                scaled = pix.scaled(self.circle_editor.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                # Determine which centre/radius to show: manual overrides take precedence
                if state.manual_center is not None and state.manual_radius is not None:
                    cx, cy = state.manual_center
                    radius = state.manual_radius
                elif state.detection is not None:
                    cx, cy = state.detection.center
                    radius = state.detection.radius
                else:
                    cx = cy = radius = 0
                # Scale coordinates to fit the displayed image
                ratio = scaled.width() / qimg.width() if qimg.width() else 1.0
                scaled_center = (int(round(cx * ratio)), int(round(cy * ratio)))
                scaled_radius = int(round(radius * ratio))
                # Update preview widget
                self.circle_editor.setImage(scaled)
                self.circle_editor.setDetection(scaled_center, scaled_radius)
                # Sync spin boxes (use original image coordinates)
                self.spin_x.blockSignals(True)
                self.spin_y.blockSignals(True)
                self.spin_radius.blockSignals(True)
                self.spin_x.setValue(cx)
                self.spin_y.setValue(cy)
                self.spin_radius.setValue(int(radius))
                self.spin_x.blockSignals(False)
                self.spin_y.blockSignals(False)
                self.spin_radius.blockSignals(False)
                return
        self.circle_editor.setImage(QPixmap())

    def _on_threshold_changed(self, value: int) -> None:
        self.view_model.dispatch(UpdateAdjustCircleThreshold(value=value))


