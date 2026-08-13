"""Sidebar controls for crop, spacing, layout, and threshold."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.layout import LayoutType
from eclipse_compositor.resources import app_icon_path
from eclipse_compositor.ui.state import MIN_RESOLUTION, JobStatus, ScreenState


class Sidebar(QWidget):
    """Parameter panel; emits intents via signals (view wires to dispatch)."""

    import_clicked = Signal()
    clear_clicked = Signal()
    preview_clicked = Signal()
    export_clicked = Signal()
    crop_size_changed = Signal(int)
    spacing_changed = Signal(float)
    layout_changed = Signal(object)
    curvature_changed = Signal(float)
    threshold_changed = Signal(int)
    grid_columns_changed = Signal(int)
    grid_rows_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._updating = False
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        icon_file = app_icon_path()
        if icon_file.is_file():
            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)
            icon_label.setPixmap(QIcon(str(icon_file)).pixmap(32, 32))
            title_row.addWidget(icon_label)
        title = QLabel("VulturEklips")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        title_row.addWidget(title)
        title_row.addStretch()
        root.addLayout(title_row)
        subtitle = QLabel("Eclipse Sequence Compositor")
        subtitle.setStyleSheet("color: #888; margin-bottom: 8px;")
        root.addWidget(subtitle)

        btn_row = QHBoxLayout()
        self.import_btn = QPushButton("Import…")
        self.clear_btn = QPushButton("Clear")
        btn_row.addWidget(self.import_btn)
        btn_row.addWidget(self.clear_btn)
        root.addLayout(btn_row)

        action_row = QHBoxLayout()
        self.preview_btn = QPushButton("Preview")
        self.export_btn = QPushButton("Export…")
        self.export_btn.setDefault(True)
        action_row.addWidget(self.preview_btn)
        action_row.addWidget(self.export_btn)
        root.addLayout(action_row)

        params = QGroupBox("Composite")
        form = QFormLayout(params)

        self.crop_slider = QSlider(Qt.Orientation.Horizontal)
        self.crop_slider.setRange(MIN_RESOLUTION, 2400)
        self.crop_slider.setSingleStep(10)
        self.crop_value = QLabel()
        form.addRow("Resolution", self._slider_row(self.crop_slider, self.crop_value))
        self.native_label = QLabel()
        self.native_label.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", self.native_label)

        # Map -50..100 → -0.50..1.00
        self.spacing_slider = QSlider(Qt.Orientation.Horizontal)
        self.spacing_slider.setRange(-50, 100)
        self.spacing_value = QLabel()
        form.addRow("Spacing", self._slider_row(self.spacing_slider, self.spacing_value))

        self.layout_combo = QComboBox()
        self.layout_combo.addItem("Linear Horizontal", LayoutType.LINEAR)
        self.layout_combo.addItem("Linear Vertical", LayoutType.VERTICAL)
        self.layout_combo.addItem("Arc", LayoutType.ARC)
        self.layout_combo.addItem("Grid", LayoutType.GRID)
        form.addRow("Layout", self.layout_combo)

        self.curve_slider = QSlider(Qt.Orientation.Horizontal)
        self.curve_slider.setRange(0, 100)  # 0.00–1.00
        self.curve_value = QLabel()
        form.addRow("Curvature", self._slider_row(self.curve_slider, self.curve_value))

        self.grid_cols_spin = QSpinBox()
        self.grid_cols_spin.setRange(1, 32)
        self.grid_cols_spin.setValue(3)
        form.addRow("Grid columns", self.grid_cols_spin)

        self.grid_rows_spin = QSpinBox()
        self.grid_rows_spin.setRange(1, 32)
        self.grid_rows_spin.setValue(2)
        form.addRow("Grid rows", self.grid_rows_spin)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(20, 250)
        self.threshold_value = QLabel()
        form.addRow("Threshold", self._slider_row(self.threshold_slider, self.threshold_value))
        root.addWidget(params)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #aaa; margin-top: 8px;")
        root.addWidget(self.status_label)

        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #e66; margin-top: 4px;")
        root.addWidget(self.error_label)

        root.addStretch(1)

        self.import_btn.clicked.connect(self.import_clicked.emit)
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        self.preview_btn.clicked.connect(self.preview_clicked.emit)
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.crop_slider.valueChanged.connect(self._on_crop)
        self.spacing_slider.valueChanged.connect(self._on_spacing)
        self.layout_combo.currentIndexChanged.connect(self._on_layout)
        self.curve_slider.valueChanged.connect(self._on_curve)
        self.threshold_slider.valueChanged.connect(self._on_threshold)
        self.grid_cols_spin.valueChanged.connect(self._on_grid_cols)
        self.grid_rows_spin.valueChanged.connect(self._on_grid_rows)

    @staticmethod
    def _slider_row(slider: QSlider, value_label: QLabel) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(slider, stretch=1)
        value_label.setMinimumWidth(48)
        lay.addWidget(value_label)
        return w

    def _on_crop(self, value: int) -> None:
        if self._updating:
            return
        self.crop_value.setText(str(value))
        self.crop_size_changed.emit(value)

    def _on_spacing(self, value: int) -> None:
        if self._updating:
            return
        spacing = value / 100.0
        self.spacing_value.setText(f"{spacing:+.2f}")
        self.spacing_changed.emit(spacing)

    def _on_layout(self, _index: int) -> None:
        if self._updating:
            return
        self.layout_changed.emit(self.layout_combo.currentData())

    def _on_curve(self, value: int) -> None:
        if self._updating:
            return
        curvature = value / 100.0
        self.curve_value.setText(f"{curvature:.2f}")
        self.curvature_changed.emit(curvature)

    def _on_threshold(self, value: int) -> None:
        if self._updating:
            return
        self.threshold_value.setText(str(value))
        self.threshold_changed.emit(value)

    def _on_grid_cols(self, value: int) -> None:
        if self._updating:
            return
        self.grid_columns_changed.emit(value)

    def _on_grid_rows(self, value: int) -> None:
        if self._updating:
            return
        self.grid_rows_changed.emit(value)

    def render(self, state: ScreenState) -> None:
        """Sync widgets from immutable state without re-emitting intents."""
        self._updating = True
        try:
            self.crop_slider.setMaximum(max(MIN_RESOLUTION, state.native_max_resolution))
            self.crop_slider.setValue(
                min(state.crop_size, state.native_max_resolution)
            )
            self.crop_value.setText(str(min(state.crop_size, state.native_max_resolution)))
            self.native_label.setText(
                f"Max native: {state.native_max_resolution}px"
            )

            spacing_i = int(round(state.spacing * 100))
            self.spacing_slider.setValue(spacing_i)
            self.spacing_value.setText(f"{state.spacing:+.2f}")
            idx = self.layout_combo.findData(state.layout)
            if idx >= 0:
                self.layout_combo.setCurrentIndex(idx)
            self.curve_slider.setValue(int(round(state.curvature * 100)))
            self.curve_value.setText(f"{state.curvature:.2f}")
            self.grid_cols_spin.setValue(state.grid_columns)
            self.grid_rows_spin.setValue(state.grid_rows)
            self.threshold_slider.setValue(state.threshold)
            self.threshold_value.setText(str(state.threshold))
            self.status_label.setText(state.status_message)
            self.error_label.setText(state.error_message or "")

            busy = (
                state.import_status == JobStatus.RUNNING
                or state.export_status == JobStatus.RUNNING
                or state.preview_status == JobStatus.RUNNING
            )
            has_images = len(state.images) > 0
            self.import_btn.setEnabled(not busy)
            self.clear_btn.setEnabled(not busy and has_images)
            self.preview_btn.setEnabled(not busy and has_images and state.proxy_ready)
            self.export_btn.setEnabled(not busy and has_images)

            is_arc = state.layout == LayoutType.ARC
            is_grid = state.layout == LayoutType.GRID
            self.curve_slider.setEnabled(is_arc)
            self.grid_cols_spin.setEnabled(is_grid)
            self.grid_rows_spin.setEnabled(is_grid)
        finally:
            self._updating = False
