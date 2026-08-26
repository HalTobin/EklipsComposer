from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap
from PySide6.QtWidgets import QWidget


class CircleEditor(QWidget):
    """Interactive preview widget allowing the user to move and resize a circle.

    The widget displays a QPixmap image and optionally a detection circle overlay.
    Coordinates passed to setDetection and emitted via geometryChanged are in
    IMAGE space (pixel coordinates of the input image pixmap).
    """

    geometryChanged = Signal(float, float, float)  # cx, cy, radius in image space

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._img_center: QPointF | None = None  # in image space coordinates
        self._img_radius: float = 0.0  # in image space pixels
        self._show_circle: bool = True
        self._dragging: bool = False
        self._last_pos: QPointF | None = None
        self.setMouseTracking(True)

    # Public API --------------------------------------------------------
    def setImage(self, pixmap: QPixmap) -> None:
        """Set the background image (empty QPixmap clears)."""
        self._pixmap = pixmap
        self.update()

    def setDetection(
        self,
        center: tuple[int, int] | tuple[float, float],
        radius: float,
        visible: bool = True,
    ) -> None:
        """Set circle parameters in IMAGE space coordinates."""
        self._img_center = QPointF(float(center[0]), float(center[1]))
        self._img_radius = float(radius)
        self._show_circle = visible
        self.update()

    # Geometry & Coordinate Transformations ----------------------------
    def _get_transform_params(self) -> tuple[float, float, float] | None:
        """Calculate scale factor and offsets to draw image aspect-fitted inside widget.

        Returns (scale, offset_x, offset_y) or None if pixmap is invalid.
        """
        if not self._pixmap or self._pixmap.isNull():
            return None
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        if img_w <= 0 or img_h <= 0:
            return None

        scale = min(self.width() / img_w, self.height() / img_h)
        target_w = img_w * scale
        target_h = img_h * scale
        offset_x = (self.width() - target_w) / 2.0
        offset_y = (self.height() - target_h) / 2.0
        return scale, offset_x, offset_y

    def _image_to_widget(self, img_cx: float, img_cy: float, img_r: float) -> tuple[QPointF, float] | None:
        params = self._get_transform_params()
        if params is None:
            return None
        scale, offset_x, offset_y = params
        widget_cx = offset_x + img_cx * scale
        widget_cy = offset_y + img_cy * scale
        widget_r = img_r * scale
        return QPointF(widget_cx, widget_cy), widget_r

    def _widget_to_image(self, pos: QPointF) -> QPointF | None:
        params = self._get_transform_params()
        if params is None:
            return None
        scale, offset_x, offset_y = params
        if scale <= 0:
            return None
        img_x = (pos.x() - offset_x) / scale
        img_y = (pos.y() - offset_y) / scale
        return QPointF(img_x, img_y)

    # Event handling ----------------------------------------------------
    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Fill background
        painter.fillRect(self.rect(), QColor("#111"))

        # 2. Draw image
        params = self._get_transform_params()
        if params is not None and self._pixmap:
            scale, offset_x, offset_y = params
            target_rect = QRectF(offset_x, offset_y, self._pixmap.width() * scale, self._pixmap.height() * scale)
            painter.drawPixmap(target_rect.toRect(), self._pixmap)

        # 3. Draw circle overlay if enabled
        if (
            self._show_circle
            and self._img_center is not None
            and self._img_radius > 0
            and params is not None
        ):
            widget_data = self._image_to_widget(
                self._img_center.x(), self._img_center.y(), self._img_radius
            )
            if widget_data is not None:
                widget_center, widget_radius = widget_data
                pen = QPen(QColor("#66ccff"), 2)
                painter.setPen(pen)
                painter.drawEllipse(widget_center, widget_radius, widget_radius)

                # Center crosshair
                cross_size = 5.0
                painter.drawLine(
                    QPointF(widget_center.x() - cross_size, widget_center.y()),
                    QPointF(widget_center.x() + cross_size, widget_center.y()),
                )
                painter.drawLine(
                    QPointF(widget_center.x(), widget_center.y() - cross_size),
                    QPointF(widget_center.x(), widget_center.y() + cross_size),
                )
        painter.end()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        params = self._get_transform_params()
        if params is None or not self._pixmap:
            return

        click_pos = event.position()
        img_pos = self._widget_to_image(click_pos)
        if img_pos is None:
            return

        if self._img_center is None:
            self._img_center = img_pos
            if self._img_radius <= 0:
                self._img_radius = max(10.0, min(self._pixmap.width(), self._pixmap.height()) * 0.1)
            self._dragging = True
            self._last_pos = click_pos
            self._emit_geometry()
            self.update()
            return

        widget_data = self._image_to_widget(
            self._img_center.x(), self._img_center.y(), self._img_radius
        )
        if widget_data is not None:
            widget_center, widget_radius = widget_data
            dist = (click_pos - widget_center).manhattanLength()
            if dist <= max(widget_radius, 15.0):
                self._dragging = True
                self._last_pos = click_pos
            else:
                self._img_center = img_pos
                self._dragging = True
                self._last_pos = click_pos
                self._emit_geometry()
                self.update()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._dragging and self._img_center is not None and self._last_pos is not None:
            params = self._get_transform_params()
            if params is not None:
                scale, _, _ = params
                if scale > 0:
                    delta_widget = event.position() - self._last_pos
                    delta_img_x = delta_widget.x() / scale
                    delta_img_y = delta_widget.y() / scale
                    self._img_center = QPointF(
                        self._img_center.x() + delta_img_x,
                        self._img_center.y() + delta_img_y,
                    )
                    self._last_pos = event.position()
                    self._emit_geometry()
                    self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._dragging = False
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        if self._img_center is None:
            return
        params = self._get_transform_params()
        if params is None:
            return
        scale, _, _ = params
        if scale <= 0:
            return

        widget_delta_r = (event.angleDelta().y() / 120.0) * 2.0
        img_delta_r = widget_delta_r / scale
        self._img_radius = max(1.0, self._img_radius + img_delta_r)
        self._emit_geometry()
        self.update()
        super().wheelEvent(event)

    # Helper -----------------------------------------------------------
    def _emit_geometry(self) -> None:
        if self._img_center is None:
            return
        self.geometryChanged.emit(self._img_center.x(), self._img_center.y(), self._img_radius)
