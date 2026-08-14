"""Sidebar controls for composite layout, colorimetry, and circular masks."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.resources import app_icon_path
from eclipse_compositor.ui.state import (
    DEFAULT_BRIGHTNESS,
    DEFAULT_CONTRAST,
    DEFAULT_GAMMA,
    DEFAULT_SATURATION,
    DEFAULT_TEMPERATURE,
    MIN_RESOLUTION,
    JobStatus,
    ScreenState,
    SidebarTab,
)


_TAB_ORDER: tuple[SidebarTab, ...] = (
    SidebarTab.COMPOSITE,
    SidebarTab.COLORIMETRY,
    SidebarTab.MASK,
)


class Sidebar(QWidget):
    """Parameter panel; emits intents via signals (view wires to dispatch)."""

    import_clicked = Signal()
    open_clicked = Signal()
    save_clicked = Signal()
    clear_clicked = Signal()
    preview_clicked = Signal()
    export_clicked = Signal()
    crop_size_changed = Signal(int)
    spacing_changed = Signal(float)
    layout_changed = Signal(object)
    direction_changed = Signal(object)
    arc_angle_changed = Signal(float)
    threshold_changed = Signal(int)
    grid_columns_changed = Signal(int)
    grid_rows_changed = Signal(int)
    sidebar_tab_changed = Signal(object)
    contrast_changed = Signal(float)
    saturation_changed = Signal(float)
    brightness_changed = Signal(float)
    gamma_changed = Signal(float)
    temperature_changed = Signal(float)
    reset_colorimetry_clicked = Signal()
    mask_enabled_changed = Signal(bool)
    mask_size_changed = Signal(float)
    mask_feather_changed = Signal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(280)
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

        btn_row = QHBoxLayout()
        self.import_btn = QPushButton("Import…")
        self.clear_btn = QPushButton("Clear")
        btn_row.addWidget(self.import_btn)
        btn_row.addWidget(self.clear_btn)
        root.addLayout(btn_row)

        project_row = QHBoxLayout()
        self.open_btn = QPushButton("Open…")
        self.save_btn = QPushButton("Save…")
        project_row.addWidget(self.open_btn)
        project_row.addWidget(self.save_btn)
        root.addLayout(project_row)

        action_row = QHBoxLayout()
        self.preview_btn = QPushButton("Preview")
        self.export_btn = QPushButton("Export…")
        self.export_btn.setDefault(True)
        action_row.addWidget(self.preview_btn)
        action_row.addWidget(self.export_btn)
        root.addLayout(action_row)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.tabs.addTab(self._build_composite_tab(), "Composite")
        self.tabs.addTab(self._build_colorimetry_tab(), "Colorimetry")
        self.tabs.addTab(self._build_mask_tab(), "Mask")
        root.addWidget(self.tabs)

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
        self.open_btn.clicked.connect(self.open_clicked.emit)
        self.save_btn.clicked.connect(self.save_clicked.emit)
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        self.preview_btn.clicked.connect(self.preview_clicked.emit)
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.tabs.currentChanged.connect(self._on_tab)
        self.crop_slider.valueChanged.connect(self._on_crop_slider)
        self.crop_editor.valueChanged.connect(self._on_crop_editor)
        self.spacing_slider.valueChanged.connect(self._on_spacing_slider)
        self.spacing_editor.valueChanged.connect(self._on_spacing_editor)
        self.layout_combo.currentIndexChanged.connect(self._on_layout)
        self.direction_combo.currentIndexChanged.connect(self._on_direction)
        self.arc_slider.valueChanged.connect(self._on_arc_slider)
        self.arc_editor.valueChanged.connect(self._on_arc_editor)
        self.threshold_slider.valueChanged.connect(self._on_threshold_slider)
        self.threshold_editor.valueChanged.connect(self._on_threshold_editor)
        self.grid_cols_spin.valueChanged.connect(self._on_grid_cols)
        self.grid_rows_spin.valueChanged.connect(self._on_grid_rows)
        self.contrast_slider.valueChanged.connect(self._on_contrast_slider)
        self.contrast_editor.valueChanged.connect(self._on_contrast_editor)
        self.saturation_slider.valueChanged.connect(self._on_saturation_slider)
        self.saturation_editor.valueChanged.connect(self._on_saturation_editor)
        self.brightness_slider.valueChanged.connect(self._on_brightness_slider)
        self.brightness_editor.valueChanged.connect(self._on_brightness_editor)
        self.gamma_slider.valueChanged.connect(self._on_gamma_slider)
        self.gamma_editor.valueChanged.connect(self._on_gamma_editor)
        self.temperature_slider.valueChanged.connect(self._on_temperature_slider)
        self.temperature_editor.valueChanged.connect(self._on_temperature_editor)
        self.reset_color_btn.clicked.connect(self.reset_colorimetry_clicked.emit)
        self.mask_enabled_check.toggled.connect(self._on_mask_enabled)
        self.mask_size_slider.valueChanged.connect(self._on_mask_size_slider)
        self.mask_size_editor.valueChanged.connect(self._on_mask_size_editor)
        self.mask_feather_slider.valueChanged.connect(self._on_mask_feather_slider)
        self.mask_feather_editor.valueChanged.connect(self._on_mask_feather_editor)

    def _build_composite_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 8, 0, 0)

        self.crop_slider = QSlider(Qt.Orientation.Horizontal)
        self.crop_slider.setRange(MIN_RESOLUTION, 2400)
        self.crop_slider.setSingleStep(10)
        self.crop_editor = self._int_field(MIN_RESOLUTION, 2400)
        form.addRow("Resolution", self._slider_row(self.crop_slider, self.crop_editor))
        self.native_label = QLabel()
        self.native_label.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", self.native_label)

        # Map -50..100 → -0.50..1.00
        self.spacing_slider = QSlider(Qt.Orientation.Horizontal)
        self.spacing_slider.setRange(-50, 100)
        self.spacing_editor = self._float_field(-0.50, 1.00, decimals=2, step=0.01)
        form.addRow("Spacing", self._slider_row(self.spacing_slider, self.spacing_editor))

        self.layout_combo = QComboBox()
        self.layout_combo.addItem("Linear", LayoutType.LINEAR)
        self.layout_combo.addItem("Arc", LayoutType.ARC)
        self.layout_combo.addItem("Grid", LayoutType.GRID)
        form.addRow("Layout", self.layout_combo)

        self.direction_combo = QComboBox()
        self.direction_combo.addItem("Horizontal →", LayoutDirection.HORIZONTAL)
        self.direction_combo.addItem("Vertical ↓", LayoutDirection.VERTICAL)
        self.direction_combo.addItem("Diagonal ↘", LayoutDirection.DIAGONAL)
        self.direction_combo.addItem("Diagonal ↙", LayoutDirection.DIAGONAL_REVERSE)
        form.addRow("Direction", self.direction_combo)

        self.arc_slider = QSlider(Qt.Orientation.Horizontal)
        self.arc_slider.setRange(-180, 180)
        self.arc_editor = self._int_field(-180, 180, suffix="°")
        form.addRow("Arc angle", self._slider_row(self.arc_slider, self.arc_editor))

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
        self.threshold_editor = self._int_field(20, 250)
        form.addRow(
            "Threshold", self._slider_row(self.threshold_slider, self.threshold_editor)
        )
        return page

    def _build_colorimetry_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 8, 0, 0)

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_editor = self._float_field(0.50, 2.00, decimals=2, step=0.01)
        form.addRow(
            "Contrast", self._slider_row(self.contrast_slider, self.contrast_editor)
        )

        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(0, 200)
        self.saturation_editor = self._float_field(0.00, 2.00, decimals=2, step=0.01)
        form.addRow(
            "Saturation",
            self._slider_row(self.saturation_slider, self.saturation_editor),
        )

        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_editor = self._int_field(-100, 100)
        form.addRow(
            "Brightness",
            self._slider_row(self.brightness_slider, self.brightness_editor),
        )

        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(50, 200)
        self.gamma_editor = self._float_field(0.50, 2.00, decimals=2, step=0.01)
        form.addRow("Gamma", self._slider_row(self.gamma_slider, self.gamma_editor))
        gamma_hint = QLabel("Above 1.0 lifts faint corona midtones.")
        gamma_hint.setWordWrap(True)
        gamma_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", gamma_hint)

        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(-100, 100)
        self.temperature_editor = self._int_field(-100, 100)
        form.addRow(
            "Temperature",
            self._slider_row(self.temperature_slider, self.temperature_editor),
        )
        temp_hint = QLabel("Negative is cooler (blue), positive is warmer (amber).")
        temp_hint.setWordWrap(True)
        temp_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", temp_hint)

        self.reset_color_btn = QPushButton("Reset to default")
        form.addRow("", self.reset_color_btn)
        return page

    def _build_mask_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 8, 0, 0)

        hint = QLabel(
            "When enabled, each frame fades to black through a circular "
            "gradient so overlapping squares lose their hard crop edges."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow(hint)

        self.mask_enabled_check = QCheckBox("Enable circular mask")
        form.addRow(self.mask_enabled_check)

        self.mask_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.mask_size_slider.setRange(0, 150)
        self.mask_size_editor = self._int_field(0, 150, suffix="%")
        form.addRow(
            "Mask size", self._slider_row(self.mask_size_slider, self.mask_size_editor)
        )
        size_hint = QLabel("100% touches the square sides; higher reaches the corners.")
        size_hint.setWordWrap(True)
        size_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", size_hint)

        self.mask_feather_slider = QSlider(Qt.Orientation.Horizontal)
        self.mask_feather_slider.setRange(0, 80)
        self.mask_feather_editor = self._int_field(0, 80, suffix="%")
        form.addRow(
            "Gradient",
            self._slider_row(self.mask_feather_slider, self.mask_feather_editor),
        )
        feather_hint = QLabel("Width of the soft fade from the image into pitch black.")
        feather_hint.setWordWrap(True)
        feather_hint.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("", feather_hint)
        return page

    @staticmethod
    def _numeric_field(box: QAbstractSpinBox) -> QAbstractSpinBox:
        """Configure a spin box as a compact, number-only text field."""
        box.setKeyboardTracking(False)
        box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        box.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        box.setFixedWidth(80)
        return box

    def _int_field(self, minimum: int, maximum: int, suffix: str = "") -> QSpinBox:
        """Integer field that rejects non-numeric input and clamps to range."""
        box = QSpinBox()
        box.setRange(minimum, maximum)
        if suffix:
            box.setSuffix(suffix)
        self._numeric_field(box)
        return box

    def _float_field(
        self,
        minimum: float,
        maximum: float,
        *,
        decimals: int = 2,
        step: float = 0.01,
    ) -> QDoubleSpinBox:
        """Decimal field that rejects non-numeric input and clamps to range."""
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(step)
        self._numeric_field(box)
        return box

    @staticmethod
    def _slider_row(slider: QSlider, editor: QWidget) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(slider, stretch=1)
        lay.addWidget(editor)
        return w

    def _on_tab(self, index: int) -> None:
        if self._updating:
            return
        if 0 <= index < len(_TAB_ORDER):
            self.sidebar_tab_changed.emit(_TAB_ORDER[index])

    def _on_crop_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.crop_editor.setValue(value)
        self._updating = False
        self.crop_size_changed.emit(value)

    def _on_crop_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.crop_slider.setValue(value)
        self._updating = False
        self.crop_size_changed.emit(value)

    def _on_spacing_slider(self, value: int) -> None:
        if self._updating:
            return
        spacing = value / 100.0
        self._updating = True
        self.spacing_editor.setValue(spacing)
        self._updating = False
        self.spacing_changed.emit(spacing)

    def _on_spacing_editor(self, value: float) -> None:
        if self._updating:
            return
        self._updating = True
        self.spacing_slider.setValue(int(round(value * 100)))
        self._updating = False
        self.spacing_changed.emit(float(value))

    def _on_layout(self, _index: int) -> None:
        if self._updating:
            return
        self.layout_changed.emit(self.layout_combo.currentData())

    def _on_direction(self, _index: int) -> None:
        if self._updating:
            return
        self.direction_changed.emit(self.direction_combo.currentData())

    def _on_arc_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.arc_editor.setValue(value)
        self._updating = False
        self.arc_angle_changed.emit(float(value))

    def _on_arc_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.arc_slider.setValue(value)
        self._updating = False
        self.arc_angle_changed.emit(float(value))

    def _on_threshold_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.threshold_editor.setValue(value)
        self._updating = False
        self.threshold_changed.emit(value)

    def _on_threshold_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.threshold_slider.setValue(value)
        self._updating = False
        self.threshold_changed.emit(value)

    def _on_grid_cols(self, value: int) -> None:
        if self._updating:
            return
        self.grid_columns_changed.emit(value)

    def _on_grid_rows(self, value: int) -> None:
        if self._updating:
            return
        self.grid_rows_changed.emit(value)

    def _emit_scaled(self, editor: QDoubleSpinBox, value: int) -> float:
        scaled = value / 100.0
        self._updating = True
        editor.setValue(scaled)
        self._updating = False
        return scaled

    def _on_contrast_slider(self, value: int) -> None:
        if self._updating:
            return
        self.contrast_changed.emit(self._emit_scaled(self.contrast_editor, value))

    def _on_contrast_editor(self, value: float) -> None:
        if self._updating:
            return
        self._updating = True
        self.contrast_slider.setValue(int(round(value * 100)))
        self._updating = False
        self.contrast_changed.emit(float(value))

    def _on_saturation_slider(self, value: int) -> None:
        if self._updating:
            return
        self.saturation_changed.emit(self._emit_scaled(self.saturation_editor, value))

    def _on_saturation_editor(self, value: float) -> None:
        if self._updating:
            return
        self._updating = True
        self.saturation_slider.setValue(int(round(value * 100)))
        self._updating = False
        self.saturation_changed.emit(float(value))

    def _on_brightness_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.brightness_editor.setValue(value)
        self._updating = False
        self.brightness_changed.emit(float(value))

    def _on_brightness_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.brightness_slider.setValue(value)
        self._updating = False
        self.brightness_changed.emit(float(value))

    def _on_gamma_slider(self, value: int) -> None:
        if self._updating:
            return
        self.gamma_changed.emit(self._emit_scaled(self.gamma_editor, value))

    def _on_gamma_editor(self, value: float) -> None:
        if self._updating:
            return
        self._updating = True
        self.gamma_slider.setValue(int(round(value * 100)))
        self._updating = False
        self.gamma_changed.emit(float(value))

    def _on_temperature_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.temperature_editor.setValue(value)
        self._updating = False
        self.temperature_changed.emit(float(value))

    def _on_temperature_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.temperature_slider.setValue(value)
        self._updating = False
        self.temperature_changed.emit(float(value))

    def _on_mask_enabled(self, checked: bool) -> None:
        if self._updating:
            return
        self.mask_enabled_changed.emit(bool(checked))

    def _on_mask_size_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.mask_size_editor.setValue(value)
        self._updating = False
        self.mask_size_changed.emit(value / 100.0)

    def _on_mask_size_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.mask_size_slider.setValue(value)
        self._updating = False
        self.mask_size_changed.emit(value / 100.0)

    def _on_mask_feather_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.mask_feather_editor.setValue(value)
        self._updating = False
        self.mask_feather_changed.emit(value / 100.0)

    def _on_mask_feather_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.mask_feather_slider.setValue(value)
        self._updating = False
        self.mask_feather_changed.emit(value / 100.0)

    def render(self, state: ScreenState) -> None:
        """Sync widgets from immutable state without re-emitting intents."""
        self._updating = True
        try:
            tab_index = _TAB_ORDER.index(state.sidebar_tab)
            self.tabs.setCurrentIndex(tab_index)

            crop_max = max(MIN_RESOLUTION, state.native_max_resolution)
            crop_value = min(state.crop_size, state.native_max_resolution)
            self.crop_slider.setMaximum(crop_max)
            self.crop_editor.setMaximum(crop_max)
            self.crop_slider.setValue(crop_value)
            self.crop_editor.setValue(crop_value)
            self.native_label.setText(
                f"Max native: {state.native_max_resolution}px"
            )

            spacing_i = int(round(state.spacing * 100))
            self.spacing_slider.setValue(spacing_i)
            self.spacing_editor.setValue(state.spacing)
            idx = self.layout_combo.findData(state.layout)
            if idx >= 0:
                self.layout_combo.setCurrentIndex(idx)
            dir_idx = self.direction_combo.findData(state.direction)
            if dir_idx >= 0:
                self.direction_combo.setCurrentIndex(dir_idx)
            angle_i = int(round(state.arc_angle))
            self.arc_slider.setValue(angle_i)
            self.arc_editor.setValue(angle_i)
            self.grid_cols_spin.setValue(state.grid_columns)
            self.grid_rows_spin.setValue(state.grid_rows)
            self.threshold_slider.setValue(state.threshold)
            self.threshold_editor.setValue(state.threshold)

            self.contrast_slider.setValue(int(round(state.contrast * 100)))
            self.contrast_editor.setValue(state.contrast)
            self.saturation_slider.setValue(int(round(state.saturation * 100)))
            self.saturation_editor.setValue(state.saturation)
            brightness_i = int(round(state.brightness))
            self.brightness_slider.setValue(brightness_i)
            self.brightness_editor.setValue(brightness_i)
            self.gamma_slider.setValue(int(round(state.gamma * 100)))
            self.gamma_editor.setValue(state.gamma)
            temperature_i = int(round(state.temperature))
            self.temperature_slider.setValue(temperature_i)
            self.temperature_editor.setValue(temperature_i)
            color_is_default = (
                abs(state.contrast - DEFAULT_CONTRAST) < 1e-6
                and abs(state.saturation - DEFAULT_SATURATION) < 1e-6
                and abs(state.brightness - DEFAULT_BRIGHTNESS) < 1e-6
                and abs(state.gamma - DEFAULT_GAMMA) < 1e-6
                and abs(state.temperature - DEFAULT_TEMPERATURE) < 1e-6
            )
            self.reset_color_btn.setEnabled(not color_is_default)

            self.mask_enabled_check.setChecked(state.mask_enabled)
            mask_size_i = int(round(state.mask_size * 100))
            self.mask_size_slider.setValue(mask_size_i)
            self.mask_size_editor.setValue(mask_size_i)
            mask_feather_i = int(round(state.mask_feather * 100))
            self.mask_feather_slider.setValue(mask_feather_i)
            self.mask_feather_editor.setValue(mask_feather_i)
            self.mask_size_slider.setEnabled(state.mask_enabled)
            self.mask_size_editor.setEnabled(state.mask_enabled)
            self.mask_feather_slider.setEnabled(state.mask_enabled)
            self.mask_feather_editor.setEnabled(state.mask_enabled)

            self.status_label.setText(state.status_message)
            self.error_label.setText(state.error_message or "")

            busy = (
                state.import_status == JobStatus.RUNNING
                or state.export_status == JobStatus.RUNNING
                or state.preview_status == JobStatus.RUNNING
            )
            has_images = len(state.images) > 0
            self.import_btn.setEnabled(not busy)
            self.open_btn.setEnabled(not busy)
            self.save_btn.setEnabled(not busy and has_images)
            self.clear_btn.setEnabled(not busy and has_images)
            self.preview_btn.setEnabled(not busy and has_images and state.proxy_ready)
            self.export_btn.setEnabled(not busy and has_images)

            is_arc = state.layout == LayoutType.ARC
            is_grid = state.layout == LayoutType.GRID
            self.direction_combo.setEnabled(not is_grid)
            self.arc_slider.setEnabled(is_arc)
            self.arc_editor.setEnabled(is_arc)
            self.grid_cols_spin.setEnabled(is_grid)
            self.grid_rows_spin.setEnabled(is_grid)
        finally:
            self._updating = False
