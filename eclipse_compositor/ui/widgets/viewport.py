"""Zoomable preview viewport for the composite image."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


def bgr_to_qimage(image: np.ndarray) -> QImage:
    """Convert a BGR uint8 NumPy array to a QImage (RGB888)."""
    if image is None or image.size == 0:
        return QImage()
    if image.ndim == 2:
        h, w = image.shape
        bytes_per_line = w
        return QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8).copy()
    rgb = image[:, :, ::-1].copy()
    h, w, _ = rgb.shape
    bytes_per_line = 3 * w
    return QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()


class PreviewViewport(QGraphicsView):
    """Center viewport that displays the composite with mouse-wheel zoom."""

    zoom_changed = Signal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self._zoom = 1.0
        self._fit_mode = True
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)

    def set_preview(self, image: np.ndarray | None, *, fit: bool = False) -> None:
        """Update the displayed composite (or clear if None).

        Args:
            image: BGR preview array.
            fit: If True, zoom so the entire image is visible in the viewport.
        """
        if image is None:
            self._pixmap_item.setPixmap(QPixmap())
            self._scene.setSceneRect(0, 0, 1, 1)
            return
        qimg = bgr_to_qimage(image)
        pix = QPixmap.fromImage(qimg)
        self._pixmap_item.setPixmap(pix)
        self._scene.setSceneRect(pix.rect())
        if fit:
            self.fit_to_view(emit=True)
        else:
            self._apply_zoom()

    def is_fit_mode(self) -> bool:
        """True when the viewport is keeping the full image visible."""
        return self._fit_mode

    def set_zoom(self, zoom: float) -> None:
        """Set absolute zoom factor from external state (exits fit mode)."""
        self._fit_mode = False
        self._zoom = max(0.01, min(8.0, zoom))
        self._apply_zoom()

    def fit_to_view(self, *, emit: bool = False) -> float:
        """Scale so the full composite is visible; return the resulting zoom."""
        if self._pixmap_item.pixmap().isNull():
            return self._zoom
        self._fit_mode = True
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = abs(self.transform().m11())
        if self._zoom <= 0:
            self._zoom = 1.0
        if emit:
            self.zoom_changed.emit(self._zoom)
        return self._zoom

    def _apply_zoom(self) -> None:
        self.resetTransform()
        self.scale(self._zoom, self._zoom)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        new_zoom = max(0.01, min(8.0, self._zoom * factor))
        if abs(new_zoom - self._zoom) < 1e-9:
            return
        self._fit_mode = False
        self._zoom = new_zoom
        self.zoom_changed.emit(self._zoom)
        self._apply_zoom()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._fit_mode and not self._pixmap_item.pixmap().isNull():
            self.fit_to_view(emit=True)
