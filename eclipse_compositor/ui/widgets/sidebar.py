"""Sidebar controls for composite layout, colorimetry, and circular masks."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.resources import app_mark_path
from eclipse_compositor.ui.state import (
    DEFAULT_BRIGHTNESS,
    DEFAULT_CONTRAST,
    DEFAULT_GAMMA,
    DEFAULT_SATURATION,
    DEFAULT_TEMPERATURE,
    MAX_MARGIN,
    MIN_MARGIN,
    MIN_RESOLUTION,
    JobStatus,
    ScreenState,
    SidebarTab,
)
from eclipse_compositor.ui.theme import (
    ActionButton,
    BrandHeader,
    ComboField,
    FloatSliderField,
    HintLabel,
    IntSliderField,
    Section,
    SegmentedControl,
    SpinField,
    StatusBanner,
    ToggleRow,
    qicon_from_path,
    scroll_page,
)

_TAB_ORDER: tuple[SidebarTab, ...] = (
    SidebarTab.COMPOSITE,
    SidebarTab.COLORIMETRY,
    SidebarTab.MASK,
    SidebarTab.CANVAS,
)

_TAB_LABELS: tuple[str, ...] = ("Composite", "Color", "Mask", "Canvas")


class Sidebar(QWidget):
    """Parameter panel; emits intents via signals (view wires to dispatch)."""

    fullscreen_clicked = Signal()
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
    margin_linked_changed = Signal(bool)
    margin_global_changed = Signal(int)
    margin_x_changed = Signal(int)
    margin_y_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(340)
        self._updating = False
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        icon = qicon_from_path(app_mark_path())
        root.addWidget(
            BrandHeader(
                "EklipsComposer",
                "by Moineaufactory",
                icon=None if icon.isNull() else icon,
            )
        )

        self.segments = SegmentedControl(_TAB_LABELS)
        root.addWidget(self.segments)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.stack.addWidget(scroll_page(self._build_composite_tab()))
        self.stack.addWidget(scroll_page(self._build_colorimetry_tab()))
        self.stack.addWidget(scroll_page(self._build_mask_tab()))
        self.stack.addWidget(scroll_page(self._build_canvas_tab()))
        root.addWidget(self.stack, stretch=1)

        run = QHBoxLayout()
        run.setSpacing(8)
        self.preview_btn = ActionButton("Full screen")
        self.preview_btn.setToolTip(
            "Inspect the composite without the editor chrome (Esc to close)."
        )
        self.export_btn = ActionButton("Export", variant="primary")
        run.addWidget(self.preview_btn)
        run.addWidget(self.export_btn)
        root.addLayout(run)

        self.status_banner = StatusBanner("muted")
        self.error_banner = StatusBanner("error")
        root.addWidget(self.status_banner)
        root.addWidget(self.error_banner)

        self.preview_btn.clicked.connect(self.fullscreen_clicked.emit)
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.segments.currentChanged.connect(self._on_tab)

        self.crop_field.valueChanged.connect(self.crop_size_changed.emit)
        self.spacing_field.valueChanged.connect(self.spacing_changed.emit)
        self.layout_field.currentDataChanged.connect(self.layout_changed.emit)
        self.direction_field.currentDataChanged.connect(self.direction_changed.emit)
        self.arc_field.valueChanged.connect(
            lambda v: self.arc_angle_changed.emit(float(v))
        )
        self.threshold_field.valueChanged.connect(self.threshold_changed.emit)
        self.grid_cols_field.valueChanged.connect(self.grid_columns_changed.emit)
        self.grid_rows_field.valueChanged.connect(self.grid_rows_changed.emit)
        self.contrast_field.valueChanged.connect(self.contrast_changed.emit)
        self.saturation_field.valueChanged.connect(self.saturation_changed.emit)
        self.brightness_field.valueChanged.connect(
            lambda v: self.brightness_changed.emit(float(v))
        )
        self.gamma_field.valueChanged.connect(self.gamma_changed.emit)
        self.temperature_field.valueChanged.connect(
            lambda v: self.temperature_changed.emit(float(v))
        )
        self.reset_color_btn.clicked.connect(self.reset_colorimetry_clicked.emit)
        self.mask_enabled_row.toggled.connect(self.mask_enabled_changed.emit)
        self.mask_size_field.valueChanged.connect(
            lambda v: self.mask_size_changed.emit(v / 100.0)
        )
        self.mask_feather_field.valueChanged.connect(
            lambda v: self.mask_feather_changed.emit(v / 100.0)
        )
        self.margin_linked_row.toggled.connect(self.margin_linked_changed.emit)
        self.margin_global_field.valueChanged.connect(self.margin_global_changed.emit)
        self.margin_x_field.valueChanged.connect(self.margin_x_changed.emit)
        self.margin_y_field.valueChanged.connect(self.margin_y_changed.emit)

    def _build_composite_tab(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 8, 0, 8)
        col.setSpacing(10)

        crop_card = Section("Frame")
        self.crop_field = IntSliderField("Resolution", MIN_RESOLUTION, 2400)
        self.native_label = HintLabel()
        self.spacing_field = FloatSliderField(
            "Spacing", -50, 100, scale=100, decimals=2
        )
        crop_card.add_widget(self.crop_field)
        crop_card.add_widget(self.native_label)
        crop_card.add_widget(self.spacing_field)
        col.addWidget(crop_card)

        layout_card = Section("Layout")
        self.layout_field = ComboField(
            "Arrangement",
            (
                ("Linear", LayoutType.LINEAR),
                ("Arc", LayoutType.ARC),
                ("Grid", LayoutType.GRID),
                ("Circle", LayoutType.CIRCLE),
            ),
        )
        self.direction_field = ComboField(
            "Direction",
            (
                ("Horizontal →", LayoutDirection.HORIZONTAL),
                ("Vertical ↓", LayoutDirection.VERTICAL),
                ("Diagonal ↘", LayoutDirection.DIAGONAL),
                ("Diagonal ↙", LayoutDirection.DIAGONAL_REVERSE),
            ),
        )
        self.arc_field = IntSliderField("Arc angle", -180, 180, suffix="°")
        grid_row = QHBoxLayout()
        grid_row.setSpacing(8)
        self.grid_cols_field = SpinField("Columns", 1, 32)
        self.grid_rows_field = SpinField("Rows", 1, 32)
        grid_row.addWidget(self.grid_cols_field)
        grid_row.addWidget(self.grid_rows_field)
        layout_card.add_widget(self.layout_field)
        layout_card.add_widget(self.direction_field)
        layout_card.add_widget(self.arc_field)
        layout_card.add_layout(grid_row)
        col.addWidget(layout_card)

        detect_card = Section("Detection")
        self.threshold_field = IntSliderField("Threshold", 20, 250)
        detect_card.add_widget(self.threshold_field)
        col.addWidget(detect_card)
        col.addStretch(1)
        return page

    def _build_colorimetry_tab(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 8, 0, 8)
        col.setSpacing(10)

        card = Section("Adjustments")
        self.contrast_field = FloatSliderField("Contrast", 50, 200)
        self.saturation_field = FloatSliderField("Saturation", 0, 200)
        self.brightness_field = IntSliderField("Brightness", -100, 100)
        self.gamma_field = FloatSliderField(
            "Gamma",
            50,
            200,
            hint="Above 1.0 lifts faint corona midtones.",
        )
        self.temperature_field = IntSliderField(
            "Temperature",
            -100,
            100,
            hint="Negative is cooler (blue), positive is warmer (amber).",
        )
        self.reset_color_btn = ActionButton("Reset to default", variant="ghost")
        card.add_widget(self.contrast_field)
        card.add_widget(self.saturation_field)
        card.add_widget(self.brightness_field)
        card.add_widget(self.gamma_field)
        card.add_widget(self.temperature_field)
        card.add_widget(self.reset_color_btn)
        col.addWidget(card)
        col.addStretch(1)
        return page

    def _build_mask_tab(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 8, 0, 8)
        col.setSpacing(10)

        card = Section("Circular mask")
        card.add_widget(
            HintLabel(
                "When enabled, each frame fades to black through a circular "
                "gradient so overlapping squares lose their hard crop edges."
            )
        )
        self.mask_enabled_row = ToggleRow("Enable circular mask")
        self.mask_size_field = IntSliderField(
            "Mask size",
            0,
            150,
            suffix="%",
            hint="100% touches the square sides; higher reaches the corners.",
        )
        self.mask_feather_field = IntSliderField(
            "Gradient",
            0,
            80,
            suffix="%",
            hint="Width of the soft fade from the image into pitch black.",
        )
        card.add_widget(self.mask_enabled_row)
        card.add_widget(self.mask_size_field)
        card.add_widget(self.mask_feather_field)
        col.addWidget(card)
        col.addStretch(1)
        return page

    def _build_canvas_tab(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 8, 0, 8)
        col.setSpacing(10)

        card = Section("Margins")
        card.add_widget(
            HintLabel(
                "Space between the laid-out frames and the canvas edge. "
                "Negative values crop into the image on that axis."
            )
        )
        self.margin_linked_row = ToggleRow("Link horizontal and vertical")
        self.margin_global_field = IntSliderField(
            "Margin",
            MIN_MARGIN,
            MAX_MARGIN,
            suffix=" px",
            tall=True,
            tick_interval=1000,
        )
        self.margin_x_field = IntSliderField(
            "Horizontal",
            MIN_MARGIN,
            MAX_MARGIN,
            suffix=" px",
            tall=True,
            tick_interval=1000,
        )
        self.margin_y_field = IntSliderField(
            "Vertical",
            MIN_MARGIN,
            MAX_MARGIN,
            suffix=" px",
            tall=True,
            tick_interval=1000,
        )
        card.add_widget(self.margin_linked_row)
        card.add_widget(self.margin_global_field)
        card.add_widget(self.margin_x_field)
        card.add_widget(self.margin_y_field)
        col.addWidget(card)
        col.addStretch(1)
        return page

    def _on_tab(self, index: int) -> None:
        if self._updating:
            return
        self.stack.setCurrentIndex(index)
        if 0 <= index < len(_TAB_ORDER):
            self.sidebar_tab_changed.emit(_TAB_ORDER[index])

    def render(self, state: ScreenState) -> None:
        """Sync widgets from immutable state without re-emitting intents."""
        self._updating = True
        try:
            tab_index = _TAB_ORDER.index(state.sidebar_tab)
            self.segments.setCurrentIndex(tab_index)
            self.stack.setCurrentIndex(tab_index)

            crop_max = max(MIN_RESOLUTION, state.native_max_resolution)
            crop_value = min(state.crop_size, state.native_max_resolution)
            self.crop_field.setRange(MIN_RESOLUTION, crop_max)
            self.crop_field.setValue(crop_value)
            self.native_label.setText(f"Max native: {state.native_max_resolution}px")

            self.spacing_field.setValue(state.spacing)
            self.layout_field.setCurrentData(state.layout)
            self.direction_field.setCurrentData(state.direction)
            self.arc_field.setValue(int(round(state.arc_angle)))
            self.grid_cols_field.setValue(state.grid_columns)
            self.grid_rows_field.setValue(state.grid_rows)
            self.threshold_field.setValue(state.threshold)

            self.contrast_field.setValue(state.contrast)
            self.saturation_field.setValue(state.saturation)
            self.brightness_field.setValue(int(round(state.brightness)))
            self.gamma_field.setValue(state.gamma)
            self.temperature_field.setValue(int(round(state.temperature)))
            color_is_default = (
                abs(state.contrast - DEFAULT_CONTRAST) < 1e-6
                and abs(state.saturation - DEFAULT_SATURATION) < 1e-6
                and abs(state.brightness - DEFAULT_BRIGHTNESS) < 1e-6
                and abs(state.gamma - DEFAULT_GAMMA) < 1e-6
                and abs(state.temperature - DEFAULT_TEMPERATURE) < 1e-6
            )
            self.reset_color_btn.setEnabled(not color_is_default)

            self.mask_enabled_row.setChecked(state.mask_enabled)
            self.mask_size_field.setValue(int(round(state.mask_size * 100)))
            self.mask_feather_field.setValue(int(round(state.mask_feather * 100)))
            self.mask_size_field.setEnabled(state.mask_enabled)
            self.mask_feather_field.setEnabled(state.mask_enabled)

            self.margin_linked_row.setChecked(state.margin_linked)
            self.margin_global_field.setValue(state.margin_x)
            self.margin_x_field.setValue(state.margin_x)
            self.margin_y_field.setValue(state.margin_y)
            linked = state.margin_linked
            self.margin_global_field.setVisible(linked)
            self.margin_x_field.setVisible(not linked)
            self.margin_y_field.setVisible(not linked)

            self.status_banner.set_message(state.status_message, kind="muted")
            self.error_banner.set_message(state.error_message or "", kind="error")

            busy = (
                state.import_status == JobStatus.RUNNING
                or state.export_status == JobStatus.RUNNING
                or state.preview_status == JobStatus.RUNNING
            )
            has_images = len(state.images) > 0
            self.preview_btn.setEnabled(state.preview_bgr is not None)
            self.export_btn.setEnabled(not busy and has_images)

            is_arc = state.layout == LayoutType.ARC
            is_grid = state.layout == LayoutType.GRID
            self.direction_field.setEnabled(not is_grid)
            self.arc_field.setEnabled(is_arc)
            self.grid_cols_field.setEnabled(is_grid)
            self.grid_rows_field.setEnabled(is_grid)
        finally:
            self._updating = False
