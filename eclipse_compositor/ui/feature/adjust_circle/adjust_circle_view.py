"""Adjust circle modal UI."""

from __future__ import annotations

import numpy as np
from pathlib import Path

from PySide6.QtCore import Qt, QSize
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
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage


class AdjustCircleView(QDialog):
    def __init__(self, view_model: AdjustCircleViewModel, state: AdjustCircleState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Adjust circle detection")
        self.setModal(True)
        self.view_model = view_model
        self.view_model.state_changed.connect(self.render)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = CaptionLabel("Adjust detected disc center")
        root.addWidget(header)

        controls = QHBoxLayout()
        self.threshold_field = IntSliderField("Threshold", 20, 250)
        self.threshold_field.valueChanged.connect(self._on_threshold_changed)
        controls.addWidget(self.threshold_field, stretch=1)

        self.auto_btn = ActionButton("Auto detect", variant="primary")
        self.auto_btn.clicked.connect(lambda: self.view_model.dispatch(AutoDetect()))
        controls.addWidget(self.auto_btn)
        root.addLayout(controls)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(QSize(680, 420))
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #444; background: #111;")
        root.addWidget(self.preview_label)

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

    def _toggle_circle(self) -> None:
        state = self.view_model.state
        self.view_model.dispatch(ToggleCircleVisibility(visible=not state.show_circle))

    def render(self, state: AdjustCircleState) -> None:
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
            self.preview_label.setPixmap(QPixmap())
            return

        image = state.image_bgr
        if isinstance(image, np.ndarray):
            qimg = bgr_to_qimage(image)
            pix = QPixmap.fromImage(qimg)
            if not pix.isNull():
                scaled = pix.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                if state.show_circle and state.detection is not None:
                    painter = QPainter(scaled)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setPen(QPen(QColor("#66ccff"), 2))
                    ratio = scaled.width() / qimg.width() if qimg.width() else 1.0
                    x = int(round(state.detection.center[0] * ratio))
                    y = int(round(state.detection.center[1] * ratio))
                    radius = int(round(state.detection.radius * ratio))
                    painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
                    painter.drawPoint(x, y)
                    painter.end()
                self.preview_label.setPixmap(scaled)
                return
        self.preview_label.setPixmap(QPixmap())
