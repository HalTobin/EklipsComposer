"""Fitted preview of the currently selected gallery frame."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.theme import COLOR, CaptionLabel
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage


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
        """Set the empty-state message."""
        self._placeholder = text
        if self._pixmap.isNull():
            self.update()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Replace the displayed image (empty pixmap clears to placeholder)."""
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
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
    """Compact preview of the currently selected gallery frame."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._last_image_ref: object | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(6)
        header = CaptionLabel("Selected frame")
        header.setObjectName("sectionTitle")
        root.addWidget(header)
        self._canvas = _FittedImage()
        root.addWidget(self._canvas, stretch=1)
        self._caption = CaptionLabel()
        self._caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._caption)
        self.setMinimumHeight(120)

    def render(self, state: ScreenState) -> None:
        """Show the selected frame proxy, or a placeholder if none."""
        index = state.selected_index
        if index is None or not (0 <= index < len(state.images)):
            self._show(None, "Select a frame", "")
            return

        item = state.images[index]
        if item.detection_ok is True:
            status = "Disc found"
        elif item.detection_ok is False:
            status = "No disc detected"
        else:
            status = "Not yet analysed"
        caption = f"{item.path.name}\n{status}"
        image = state.selected_preview_bgr
        if image is not None and not isinstance(image, np.ndarray):
            image = None
        self._show(image, "Preview unavailable", caption)

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
