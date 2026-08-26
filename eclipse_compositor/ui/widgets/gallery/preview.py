"""Fitted preview and styled EXIF properties of the currently selected gallery frame."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.theme import COLOR, ActionButton, CaptionLabel, FieldLabel
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage


def _as_text(value: object) -> str:
    """Convert EXIF payload values to a readable string."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        for encoding in ("utf-8", "latin-1", "windows-1252"):
            try:
                return value.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        return value.decode("utf-8", errors="replace").strip()
    if isinstance(value, (list, tuple)):
        return ", ".join(_as_text(part) for part in value if _as_text(part))
    return str(value).strip()


def _gps_to_text(gps_info: object) -> str:
    """Convert GPS EXIF data to a human-readable location string."""
    if not isinstance(gps_info, dict):
        return "Not available"

    def _coord(tag: int, ref_tag: int) -> str | None:
        values = gps_info.get(tag)
        ref = gps_info.get(ref_tag)
        if values is None or ref is None:
            return None
        if isinstance(values, tuple):
            parts = values
        elif isinstance(values, list):
            parts = tuple(values)
        else:
            parts = (values,)
        try:
            total = float(parts[0])
            for part in parts[1:]:
                total += float(part) / 60.0
        except (TypeError, ValueError):
            return None
        suffix = str(ref)
        return f"{total:.6f} {suffix}"

    lat = _coord(2, 1)
    lon = _coord(4, 3)
    if lat is None and lon is None:
        return "Not available"
    if lat is None:
        lat = "Unknown"
    if lon is None:
        lon = "Unknown"
    return f"{lat}, {lon}"


def read_image_properties(path: str | Path) -> dict[str, str]:
    """Read EXIF and image metadata for a selected frame."""
    file_path = Path(path)
    props: dict[str, str] = {
        "File": str(file_path.name),
        "Resolution": "Unknown",
        "Date": "Not available",
        "Comment": "Not available",
        "Location": "Not available",
        "Camera": "Not available",
    }

    try:
        with Image.open(file_path) as image:
            width, height = image.size
            props["Resolution"] = f"{width} × {height}"

            exif = image.getexif()
            if exif:
                date_values = (
                    exif.get(36867),
                    exif.get(306),
                    exif.get(36868),
                )
                for value in date_values:
                    text = _as_text(value)
                    if text:
                        if text.count(":") >= 2 and " " in text:
                            try:
                                from datetime import datetime

                                dt = datetime.strptime(text, "%Y:%m:%d %H:%M:%S")
                                props["Date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                props["Date"] = text
                        else:
                            props["Date"] = text
                        break

                comment_text = _as_text(exif.get(270) or exif.get(37510))
                if comment_text:
                    props["Comment"] = comment_text
                camera_maker = _as_text(exif.get(271))
                camera_model = _as_text(exif.get(272))
                camera = ", ".join(part for part in (camera_maker, camera_model) if part)
                if camera:
                    props["Camera"] = camera

                gps_info = exif.get_ifd(34853)
                if gps_info:
                    location = _gps_to_text(gps_info)
                    if location != "Not available":
                        props["Location"] = location

                if not props["Comment"] or props["Comment"] == "Not available":
                    artist = _as_text(exif.get(315))
                    if artist:
                        props["Comment"] = artist
    except (OSError, ValueError):
        return props

    return props


class _FittedImage(QWidget):
    """Paints a pixmap letterboxed into a rounded well."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._placeholder = "Select a frame"
        self.setMinimumSize(80, 80)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def set_placeholder(self, text: str) -> None:
        self._placeholder = text
        if self._pixmap.isNull():
            self.update()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.rect().adjusted(0, 0, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        painter.setClipPath(path)
        painter.fillPath(path, QColor(COLOR.bg_sunken))
        if self._pixmap.isNull():
            painter.setPen(QColor(COLOR.text_faint))
            painter.drawText(
                self.rect(),
                int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
                self._placeholder,
            )
            return
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)


class FramePreview(QWidget):
    """Compact preview and metadata tabs for the currently selected gallery frame."""

    adjust_circle_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_image_ref: object | None = None
        self._selected_path: Path | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 0)
        root.setSpacing(4)

        header = FieldLabel("SELECTED FRAME")
        root.addWidget(header)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._tabs.setDocumentMode(True)

        self._preview_widget = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_widget)
        self._preview_layout.setContentsMargins(0, 4, 0, 0)
        self._preview_layout.setSpacing(4)
        self._canvas = _FittedImage()
        self._preview_layout.addWidget(self._canvas, stretch=1)
        self._caption = CaptionLabel()
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_layout.addWidget(self._caption)

        self.adjust_circle_btn = ActionButton("Adjust Circle...", variant="secondary")
        self.adjust_circle_btn.setToolTip("Fine-tune disc center and radius detection for this frame")
        self.adjust_circle_btn.setFixedHeight(28)
        self.adjust_circle_btn.clicked.connect(self.adjust_circle_requested.emit)
        self.adjust_circle_btn.setEnabled(False)
        self._preview_layout.addWidget(self.adjust_circle_btn)

        self._properties_widget = QWidget()
        self._properties_layout = QVBoxLayout(self._properties_widget)
        self._properties_layout.setContentsMargins(6, 6, 6, 6)
        self._properties_label = QLabel()
        self._properties_label.setWordWrap(True)
        self._properties_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._properties_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._properties_layout.addWidget(self._properties_label)

        self._tabs.addTab(self._preview_widget, "Preview")
        self._tabs.addTab(self._properties_widget, "Properties")
        root.addWidget(self._tabs, stretch=1)
        self.setMinimumHeight(150)

    def render(self, state: ScreenState) -> None:
        """Show the selected frame proxy and metadata, or a placeholder if none."""
        index = state.selected_index
        if index is None or not (0 <= index < len(state.images)):
            self.adjust_circle_btn.setEnabled(False)
            self._show(None, "Select a frame", "")
            self._set_properties_text("<p style='color:#6A7080; padding:4px;'>Select a frame to inspect its EXIF and file details.</p>")
            return

        self.adjust_circle_btn.setEnabled(True)
        item = state.images[index]
        self._selected_path = item.path
        if item.detection_ok is True:
            status = f"<span style='color: {COLOR.success};'>● Disc found</span>"
        elif item.detection_ok is False:
            status = f"<span style='color: {COLOR.danger};'>⚠ No disc detected</span>"
        else:
            status = f"<span style='color: {COLOR.text_faint};'>Ready</span>"
        caption = f"<b>{item.path.name}</b> · {status}"
        image = state.selected_preview_bgr
        if image is not None and not isinstance(image, np.ndarray):
            image = None
        self._show(image, "Preview unavailable", caption)
        self._set_properties_text(self._properties_html(item.path))

    def _properties_html(self, path: Path) -> str:
        """Create a styled table summary for the selected frame's metadata."""
        properties = read_image_properties(path)
        rows = [
            f"<tr>"
            f"<td style='color: {COLOR.text_muted}; font-size: 11px; font-weight: 600; padding: 2px 4px;'>{label.upper()}</td>"
            f"<td style='color: {COLOR.text}; font-size: 11px; padding: 2px 4px;'>{value}</td>"
            f"</tr>"
            for label, value in properties.items()
            if value and value != "Not available"
        ]
        if not rows:
            return "<p style='color:#6A7080;'><i>No metadata available for this frame.</i></p>"
        return f"<table style='width: 100%; border-collapse: collapse;'>{''.join(rows)}</table>"

    def _set_properties_text(self, text: str) -> None:
        self._properties_label.setText(text)

    def show_properties(self) -> None:
        self._tabs.setCurrentIndex(1)

    def _show(
        self,
        image: np.ndarray | None,
        placeholder: str,
        caption: str,
    ) -> None:
        self._caption.setText(caption)
        self._canvas.set_placeholder(placeholder)
        if image is self._last_image_ref:
            return
        self._last_image_ref = image
        if image is None:
            self._canvas.set_pixmap(QPixmap())
            return
        qimg = bgr_to_qimage(image)
        self._canvas.set_pixmap(QPixmap.fromImage(qimg))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._canvas.update()
