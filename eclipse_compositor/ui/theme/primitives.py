"""Reusable presentation widgets built on the EklipsComposer theme tokens."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.drop_import import mime_has_importable_paths, paths_from_mime
from eclipse_compositor.ui.theme.tokens import COLOR, RADIUS, SPACE


def refresh_property(widget: QWidget, name: str, value: object) -> None:
    """Set a dynamic Qt property and restyle the widget immediately."""
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class FieldLabel(QLabel):
    """Small caps-like label sitting above a control."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text.upper(), parent)
        self.setObjectName("fieldLabel")


class HintLabel(QLabel):
    """Secondary helper copy under a control."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("hintLabel")
        self.setWordWrap(True)


class CaptionLabel(QLabel):
    """Compact meta text (counts, filenames, zoom)."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("captionLabel")
        self.setWordWrap(True)


class StatusBanner(QLabel):
    """Status / error strip. Hidden when the text is empty."""

    def __init__(self, kind: str = "muted", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWordWrap(True)
        self.set_kind(kind)
        self.hide()

    def set_kind(self, kind: str) -> None:
        """Switch visual treatment: ``muted``, ``error``, or ``success``."""
        refresh_property(self, "banner", kind)

    def set_message(self, text: str, *, kind: str | None = None) -> None:
        """Update copy and visibility. Pass ``kind`` to restyle at the same time."""
        if kind is not None:
            self.set_kind(kind)
        self.setText(text)
        self.setVisible(bool(text.strip()))


def qicon_from_path(path: Path | str, *, size: int = 256) -> QIcon:
    """Load *path* via Pillow so frozen builds don't need Qt image plugins.

    The packaged app strips ``libqicns`` / ``libqico`` / ``libqsvg``. PNG is
    built into QtGui, but decoding here keeps alpha and one code path for
    every format Pillow can read.
    """
    file = Path(path)
    if not file.is_file():
        return QIcon()
    try:
        from PIL import Image
    except ImportError:
        pix = QPixmap(str(file))
        if pix.isNull():
            return QIcon()
        return QIcon(pix)
    try:
        with Image.open(file) as src:
            rgba = src.convert("RGBA").copy()
    except OSError:
        return QIcon()
    rgba.thumbnail((size, size), Image.Resampling.LANCZOS)
    w, h = rgba.size
    qimg = QImage(rgba.tobytes(), w, h, 4 * w, QImage.Format.Format_RGBA8888).copy()
    pix = QPixmap.fromImage(qimg)
    if pix.isNull():
        return QIcon()
    return QIcon(pix)


class ActionButton(QPushButton):
    """Themed button. ``variant`` is ``primary``, ``secondary``, ``ghost``, or ``hud``."""

    def __init__(
        self,
        text: str = "",
        *,
        variant: str = "secondary",
        icon: QIcon | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("variant", variant)
        if variant == "primary":
            self.setDefault(True)
        if icon is not None and not icon.isNull():
            self.setIcon(icon)


class BrandHeader(QWidget):
    """App mark + title + one-line subtitle."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: QIcon | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)
        if icon is not None and not icon.isNull():
            mark = QLabel()
            mark.setFixedSize(36, 36)
            mark.setPixmap(icon.pixmap(36, 36))
            row.addWidget(mark, alignment=Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        title_lab = QLabel(title)
        title_lab.setObjectName("brandTitle")
        col.addWidget(title_lab)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("brandSubtitle")
            col.addWidget(sub)
        row.addLayout(col, stretch=1)


class Section(QFrame):
    """Raised card that groups related controls."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("section")
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.md, SPACE.md, SPACE.md, SPACE.md)
        root.setSpacing(SPACE.sm)
        if title:
            heading = QLabel(title)
            heading.setObjectName("sectionTitle")
            root.addWidget(heading)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(SPACE.md)
        root.addLayout(self.body)

    def add_widget(self, widget: QWidget) -> None:
        """Append a child to the card body."""
        self.body.addWidget(widget)

    def add_layout(self, layout: QLayout) -> None:
        """Append a nested layout to the card body."""
        self.body.addLayout(layout)


class SegmentedControl(QFrame):
    """Exclusive text segments, used as sidebar page tabs."""

    currentChanged = Signal(int)

    def __init__(
        self,
        labels: Sequence[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("segmentedControl")
        self._updating = False
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(2)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: list[QPushButton] = []
        for index, label in enumerate(labels):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setProperty("variant", "segment")
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            self._group.addButton(button, index)
            row.addWidget(button)
            self._buttons.append(button)
        if self._buttons:
            self._buttons[0].setChecked(True)
        self._group.idClicked.connect(self._on_id)

    def currentIndex(self) -> int:
        """Return the checked segment index."""
        return max(0, self._group.checkedId())

    def setCurrentIndex(self, index: int) -> None:
        """Select a segment without emitting ``currentChanged``."""
        if not (0 <= index < len(self._buttons)):
            return
        self._updating = True
        try:
            self._buttons[index].setChecked(True)
        finally:
            self._updating = False

    def _on_id(self, index: int) -> None:
        if self._updating:
            return
        self.currentChanged.emit(index)


class ToggleSwitch(QWidget):
    """Compact animated on/off switch."""

    toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._knob = 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def isChecked(self) -> bool:
        """Return whether the switch is on."""
        return self._checked

    def setChecked(self, checked: bool, *, animate: bool = True) -> None:
        """Set the switch. Does not emit ``toggled``."""
        checked = bool(checked)
        if checked == self._checked:
            self._knob = 1.0 if checked else 0.0
            self.update()
            return
        self._checked = checked
        target = 1.0 if checked else 0.0
        if animate and self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._knob)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._knob = target
            self.update()

    def get_knob(self) -> float:
        """Animation position in 0..1 (Qt property)."""
        return self._knob

    def set_knob(self, value: float) -> None:
        """Animation position in 0..1 (Qt property)."""
        self._knob = float(value)
        self.update()

    knob = Property(float, get_knob, set_knob)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            target = 1.0 if self._checked else 0.0
            self._anim.stop()
            self._anim.setStartValue(self._knob)
            self._anim.setEndValue(target)
            self._anim.start()
            self.toggled.emit(self._checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = self.rect().adjusted(1, 1, -1, -1)
        off = QColor(COLOR.border_strong)
        on = QColor(COLOR.accent)
        fill = QColor(
            int(off.red() + (on.red() - off.red()) * self._knob),
            int(off.green() + (on.green() - off.green()) * self._knob),
            int(off.blue() + (on.blue() - off.blue()) * self._knob),
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(track, track.height() / 2, track.height() / 2)
        margin = 2
        knob_d = track.height() - margin * 2
        travel = track.width() - knob_d - margin * 2
        x = track.x() + margin + travel * self._knob
        y = track.y() + margin
        painter.setBrush(QColor(COLOR.accent_text if self._knob > 0.5 else COLOR.text))
        painter.drawEllipse(int(x), int(y), knob_d, knob_d)


class ToggleRow(QWidget):
    """Switch with a clickable label, used for boolean settings."""

    toggled = Signal(bool)

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._updating = False
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)
        self._switch = ToggleSwitch()
        self._label = QLabel(text)
        self._label.setWordWrap(True)
        row.addWidget(self._switch)
        row.addWidget(self._label, stretch=1)
        self._switch.toggled.connect(self._on_switch)
        self._label.installEventFilter(self)

    def isChecked(self) -> bool:
        """Return whether the row is on."""
        return self._switch.isChecked()

    def setChecked(self, checked: bool) -> None:
        """Set the switch without emitting ``toggled``."""
        self._updating = True
        try:
            self._switch.setChecked(checked, animate=False)
        finally:
            self._updating = False

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self._label and event.type() == QEvent.Type.MouseButtonPress:
            self._switch.setChecked(not self._switch.isChecked())
            self.toggled.emit(self._switch.isChecked())
            return True
        return super().eventFilter(watched, event)

    def _on_switch(self, checked: bool) -> None:
        if self._updating:
            return
        self.toggled.emit(checked)


class EclipseMark(QWidget):
    """Decorative diamond-ring mark for empty states."""

    def __init__(self, size: int = 72, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = self._size * 0.28
        glow = QRadialGradient(center, radius * 1.85)
        glow.setColorAt(0.35, QColor(255, 201, 74, 80))
        glow.setColorAt(1.0, QColor(255, 201, 74, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(center, int(radius * 1.85), int(radius * 1.85))
        painter.setPen(QPen(QColor(COLOR.accent), 2.4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, int(radius), int(radius))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLOR.bg_app))
        offset = QPoint(int(radius * 0.22), 0)
        painter.drawEllipse(center + offset, int(radius - 1), int(radius - 1))


class EmptyState(QWidget):
    """Centered title, hint, and Import action over an eclipse mark."""

    import_clicked = Signal()
    files_dropped = Signal(object)  # tuple[Path, ...]
    drop_hover_changed = Signal(bool)

    def __init__(
        self,
        title: str,
        hint: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        col = QVBoxLayout(self)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.setSpacing(SPACE.sm)
        col.addWidget(EclipseMark(), alignment=Qt.AlignmentFlag.AlignCenter)
        title_lab = QLabel(title)
        title_lab.setObjectName("emptyTitle")
        title_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title_lab)
        if hint:
            hint_lab = HintLabel(hint)
            hint_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_lab.setMaximumWidth(320)
            col.addWidget(hint_lab, alignment=Qt.AlignmentFlag.AlignCenter)
        self._import_btn = ActionButton("Import", variant="primary")
        self._import_btn.clicked.connect(self.import_clicked.emit)
        col.addSpacing(SPACE.md)
        col.addWidget(self._import_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_import_enabled(self, enabled: bool) -> None:
        """Enable or disable the empty-state Import button."""
        self._import_btn.setEnabled(enabled)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.drop_hover_changed.emit(True)
            return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.drop_hover_changed.emit(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self.drop_hover_changed.emit(False)
        if mime_has_importable_paths(event.mimeData()):
            paths = paths_from_mime(event.mimeData())
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            if paths:
                self.files_dropped.emit(tuple(paths))
            return
        event.ignore()


class ZoomHud(QFrame):
    """Floating Fit / percentage / 1:1 control for the preview viewport."""

    fit_clicked = Signal()
    actual_clicked = Signal()
    full_clicked = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        show_full: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("zoomHud")
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(2)
        fit = ActionButton("Fit", variant="hud")
        actual = ActionButton("1:1", variant="hud")
        self._label = CaptionLabel("Fit")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumWidth(44)
        fit.clicked.connect(self.fit_clicked.emit)
        actual.clicked.connect(self.actual_clicked.emit)
        row.addWidget(fit)
        row.addWidget(self._label)
        row.addWidget(actual)
        if show_full:
            full = ActionButton("Full", variant="hud")
            full.setToolTip("Inspect the composite full screen")
            full.clicked.connect(self.full_clicked.emit)
            row.addWidget(full)

    def set_zoom(self, zoom: float, *, fit: bool) -> None:
        """Update the percentage label. Shows ``Fit`` while in fit mode."""
        self._label.setText("Fit" if fit else f"{zoom:.0%}")


def _configure_compact_spin(box: QAbstractSpinBox, *, width: int = 80) -> None:
    """Make a spin box behave as a compact numeric text field."""
    box.setKeyboardTracking(False)
    box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    box.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
    box.setFixedWidth(width)
    box.setObjectName("compactSpin")


class IntSliderField(QWidget):
    """Labeled integer slider with a compact numeric editor."""

    valueChanged = Signal(int)

    def __init__(
        self,
        label: str,
        minimum: int,
        maximum: int,
        *,
        suffix: str = "",
        hint: str = "",
        tall: bool = False,
        tick_interval: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._updating = False
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs)
        if label:
            col.addWidget(FieldLabel(label))

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        if tall:
            self.slider.setMinimumHeight(36)
            self.slider.setProperty("tall", True)
            self.slider.setPageStep(100)
        if tick_interval:
            self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            self.slider.setTickInterval(tick_interval)

        self.editor = QSpinBox()
        self.editor.setRange(minimum, maximum)
        if suffix:
            self.editor.setSuffix(suffix)
        _configure_compact_spin(self.editor, width=110 if suffix else 80)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)
        row.addWidget(self.slider, stretch=1)
        row.addWidget(self.editor)
        col.addLayout(row)
        if hint:
            col.addWidget(HintLabel(hint))

        self.slider.valueChanged.connect(self._on_slider)
        self.editor.valueChanged.connect(self._on_editor)

    def value(self) -> int:
        """Return the current integer value."""
        return int(self.slider.value())

    def setValue(self, value: int) -> None:
        """Set slider and editor without emitting ``valueChanged``."""
        self._updating = True
        try:
            self.slider.setValue(int(value))
            self.editor.setValue(int(value))
        finally:
            self._updating = False

    def setRange(self, minimum: int, maximum: int) -> None:
        """Update the allowed integer range without emitting ``valueChanged``."""
        self._updating = True
        try:
            self.slider.setRange(minimum, maximum)
            self.editor.setRange(minimum, maximum)
        finally:
            self._updating = False

    def _on_slider(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.editor.setValue(value)
        self._updating = False
        self.valueChanged.emit(value)

    def _on_editor(self, value: int) -> None:
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(value)
        self._updating = False
        self.valueChanged.emit(value)


class FloatSliderField(QWidget):
    """Slider stored as ints, editor and emitted value scaled by ``scale``."""

    valueChanged = Signal(float)

    def __init__(
        self,
        label: str,
        slider_min: int,
        slider_max: int,
        *,
        scale: int = 100,
        decimals: int = 2,
        hint: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._updating = False
        self._scale = scale
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs)
        if label:
            col.addWidget(FieldLabel(label))

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(slider_min, slider_max)

        self.editor = QDoubleSpinBox()
        self.editor.setRange(slider_min / scale, slider_max / scale)
        self.editor.setDecimals(decimals)
        self.editor.setSingleStep(10 ** (-decimals))
        _configure_compact_spin(self.editor)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)
        row.addWidget(self.slider, stretch=1)
        row.addWidget(self.editor)
        col.addLayout(row)
        if hint:
            col.addWidget(HintLabel(hint))

        self.slider.valueChanged.connect(self._on_slider)
        self.editor.valueChanged.connect(self._on_editor)

    def value(self) -> float:
        """Return the scaled floating-point value."""
        return self.slider.value() / self._scale

    def setValue(self, value: float) -> None:
        """Set slider and editor without emitting ``valueChanged``."""
        self._updating = True
        try:
            self.slider.setValue(int(round(value * self._scale)))
            self.editor.setValue(float(value))
        finally:
            self._updating = False

    def _on_slider(self, value: int) -> None:
        if self._updating:
            return
        scaled = value / self._scale
        self._updating = True
        self.editor.setValue(scaled)
        self._updating = False
        self.valueChanged.emit(scaled)

    def _on_editor(self, value: float) -> None:
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(int(round(value * self._scale)))
        self._updating = False
        self.valueChanged.emit(float(value))


class ComboField(QWidget):
    """Labeled combo box that emits item data (not the display string)."""

    currentDataChanged = Signal(object)

    def __init__(
        self,
        label: str,
        items: Sequence[tuple[str, object]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._updating = False
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs)
        if label:
            col.addWidget(FieldLabel(label))
        self.combo = QComboBox()
        for text, data in items:
            self.combo.addItem(text, data)
        col.addWidget(self.combo)
        self.combo.currentIndexChanged.connect(self._on_index)

    def currentData(self) -> object:
        """Return the data role of the current item."""
        return self.combo.currentData()

    def setCurrentData(self, data: object) -> None:
        """Select the item whose data matches ``data`` without emitting."""
        index = self.combo.findData(data)
        if index < 0:
            return
        self._updating = True
        try:
            self.combo.setCurrentIndex(index)
        finally:
            self._updating = False

    def _on_index(self, _index: int) -> None:
        if self._updating:
            return
        self.currentDataChanged.emit(self.combo.currentData())


class SpinField(QWidget):
    """Labeled spin box with stepper arrows (for small integer counts)."""

    valueChanged = Signal(int)

    def __init__(
        self,
        label: str,
        minimum: int,
        maximum: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._updating = False
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs)
        if label:
            col.addWidget(FieldLabel(label))
        self.spin = QSpinBox()
        self.spin.setRange(minimum, maximum)
        col.addWidget(self.spin)
        self.spin.valueChanged.connect(self._on_value)

    def value(self) -> int:
        """Return the current integer."""
        return int(self.spin.value())

    def setValue(self, value: int) -> None:
        """Set the spin box without emitting ``valueChanged``."""
        self._updating = True
        try:
            self.spin.setValue(int(value))
        finally:
            self._updating = False

    def _on_value(self, value: int) -> None:
        if self._updating:
            return
        self.valueChanged.emit(value)


def scroll_page(page: QWidget) -> QScrollArea:
    """Wrap a tab page so short windows can still reach every control."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(page)
    area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return area
