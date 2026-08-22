from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap
from PySide6.QtWidgets import QWidget


class CircleEditor(QWidget):
    """Interactive preview widget allowing the user to move and resize a circle.

    The widget displays a QPixmap image and optionally a detection circle.
    Users can drag the circle centre with the mouse and adjust its radius using the mouse wheel.
    Geometry changes are emitted via the ``geometryChanged`` signal as ``(center_x, center_y, radius)``.
    """

    geometryChanged = Signal(float, float, float)  # cx, cy, radius

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._center: QPointF | None = None  # widget coordinates
        self._radius: float = 0.0
        self._dragging: bool = False
        self.setMouseTracking(True)

    # Public API --------------------------------------------------------
    def setImage(self, pixmap: QPixmap) -> None:
        """Set the background image (empty QPixmap clears)."""
        self._pixmap = pixmap
        self.update()

    def setDetection(self, center: tuple[int, int], radius: int) -> None:
        """Set the circle to be drawn (coordinates are in widget space)."""
        self._center = QPointF(float(center[0]), float(center[1]))
        self._radius = float(radius)
        self.update()

    # Event handling ----------------------------------------------------
    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # draw background image scaled preserving aspect ratio
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # centre the image within the widget
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        # draw circle overlay
        if self._center is not None and self._radius > 0:
            pen = QPen(QColor("#66ccff"), 2)
            painter.setPen(pen)
            painter.drawEllipse(self._center, self._radius, self._radius)
        painter.end()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if self._center is None:
            # start a new centre at click position
            self._center = event.position()
            self._dragging = True
            self._last_pos = event.position()
            self._emit_geometry()
            return
        # if click near existing centre, start dragging
        dist = (event.position() - self._center).manhattanLength()
        if dist <= max(self._radius, 5):
            self._dragging = True
            self._last_pos = event.position()
        else:
            # create new centre
            self._center = event.position()
            self._dragging = True
            self._last_pos = event.position()
            self._emit_geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._dragging and self._center is not None:
            delta = event.position() - self._last_pos
            self._center += delta
            self._last_pos = event.position()
            self._emit_geometry()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._dragging = False
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        if self._center is None:
            return
        # each wheel notch (120) changes radius by 1 pixel
        delta = event.angleDelta().y() / 120
        self._radius = max(1.0, self._radius + delta)
        self._emit_geometry()
        self.update()
        super().wheelEvent(event)

    # Helper -----------------------------------------------------------
    def _emit_geometry(self) -> None:
        if self._center is None:
            return
        self.geometryChanged.emit(self._center.x(), self._center.y(), self._radius)
