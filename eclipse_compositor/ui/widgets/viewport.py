"""Zoomable preview viewport for the composite image."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QImage,
    QMouseEvent,
    QNativeGestureEvent,
    QPixmap,
    QResizeEvent,
    QShowEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QGestureEvent,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QPinchGesture,
    QWidget,
)

from eclipse_compositor.ui.drop_import import mime_has_importable_paths, paths_from_mime
from eclipse_compositor.ui.theme import COLOR, EmptyState, ZoomHud

_VIEWPORT_BG = QColor(COLOR.bg_viewport)
_MIN_ZOOM = 0.01
_MAX_ZOOM = 8.0


def _native_gesture_type(*names: str) -> object | None:
    """Resolve a NativeGestureType member (names differ across Qt 6 versions)."""
    enum = Qt.NativeGestureType
    for name in names:
        value = getattr(enum, name, None)
        if value is not None:
            return value
    return None


_ZOOM_GESTURE = _native_gesture_type("ZoomNativeGesture", "Zoom")
_SMART_ZOOM_GESTURE = _native_gesture_type("SmartZoomNativeGesture", "SmartZoom")
_BEGIN_GESTURE = _native_gesture_type("BeginNativeGesture")
_END_GESTURE = _native_gesture_type("EndNativeGesture")


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
    """Center viewport that displays the composite with mouse-wheel / pinch zoom."""

    zoom_changed = Signal(float)
    files_dropped = Signal(object)  # tuple[Path, ...]
    drop_hover_changed = Signal(bool)

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
        # Mid-gray around the pixmap so the black composite canvas is visible.
        self.setBackgroundBrush(_VIEWPORT_BG)
        self._scene.setBackgroundBrush(_VIEWPORT_BG)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setAcceptDrops(True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.grabGesture(Qt.GestureType.PinchGesture)
        self.viewport().grabGesture(Qt.GestureType.PinchGesture)
        self.viewport().installEventFilter(self)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.drop_hover_changed.emit(True)
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return
        super().dragMoveEvent(event)

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
        super().dropEvent(event)

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

    def current_zoom(self) -> float:
        """Return the current absolute zoom factor."""
        return self._zoom

    def has_preview(self) -> bool:
        """True when a composite pixmap is currently displayed."""
        return not self._pixmap_item.pixmap().isNull()

    def zoom_to_actual(self) -> None:
        """User intent: zoom to 100% (exits fit mode)."""
        self._set_zoom_from_user(1.0)

    def set_zoom(self, zoom: float) -> None:
        """Set absolute zoom factor from external state (exits fit mode)."""
        self._fit_mode = False
        self._zoom = max(_MIN_ZOOM, min(_MAX_ZOOM, zoom))
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

    def _set_zoom_from_user(self, zoom: float) -> None:
        new_zoom = max(_MIN_ZOOM, min(_MAX_ZOOM, zoom))
        if abs(new_zoom - self._zoom) < 1e-9:
            return
        self._fit_mode = False
        self._zoom = new_zoom
        self.zoom_changed.emit(self._zoom)
        self._apply_zoom()

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self.viewport() and event.type() == QEvent.Type.NativeGesture:
            return self._on_native_gesture(event)
        return super().eventFilter(watched, event)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.NativeGesture:
            return self._on_native_gesture(event)
        if event.type() == QEvent.Type.Gesture:
            return self._on_pinch_gesture(event)
        return super().event(event)

    def viewportEvent(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.NativeGesture:
            return self._on_native_gesture(event)
        if event.type() == QEvent.Type.Gesture:
            return self._on_pinch_gesture(event)
        return super().viewportEvent(event)

    def _on_pinch_gesture(self, event: QEvent) -> bool:
        if not isinstance(event, QGestureEvent):
            return False
        pinch = event.gesture(Qt.GestureType.PinchGesture)
        if pinch is None or not isinstance(pinch, QPinchGesture):
            return False
        if pinch.state() in (
            Qt.GestureState.GestureUpdated,
            Qt.GestureState.GestureFinished,
        ):
            factor = float(pinch.scaleFactor())
            if factor > 0.0 and abs(factor - 1.0) > 1e-6:
                self._set_zoom_from_user(self._zoom * factor)
        return True

    def _on_native_gesture(self, event: QEvent) -> bool:
        if not isinstance(event, QNativeGestureEvent):
            return False
        kind = event.gestureType()
        if _BEGIN_GESTURE is not None and kind == _BEGIN_GESTURE:
            return True
        if _END_GESTURE is not None and kind == _END_GESTURE:
            return True
        if _SMART_ZOOM_GESTURE is not None and kind == _SMART_ZOOM_GESTURE:
            self._toggle_fit_zoom()
            return True
        if _ZOOM_GESTURE is not None and kind == _ZOOM_GESTURE:
            factor = 1.0 + float(event.value())
            if factor > 0.0:
                self._set_zoom_from_user(self._zoom * factor)
            return True
        return False

    def _toggle_fit_zoom(self) -> None:
        """Two-finger double-tap / mouse double-click: fit, or 100% if already fitted."""
        if self._pixmap_item.pixmap().isNull():
            return
        if self._fit_mode:
            self._set_zoom_from_user(1.0)
        else:
            self.fit_to_view(emit=True)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_fit_zoom()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            delta = event.pixelDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 1 / 1.15
        self._set_zoom_from_user(self._zoom * factor)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._fit_mode and not self._pixmap_item.pixmap().isNull():
            self.fit_to_view(emit=True)


class ViewportPane(QWidget):
    """Preview surface with empty state, drop highlight, and a zoom HUD."""

    zoom_changed = Signal(float)
    files_dropped = Signal(object)  # tuple[Path, ...]
    full_clicked = Signal()
    import_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("viewportPane")
        self.view = PreviewViewport(self)
        self.empty = EmptyState(
            "Drop eclipse photos here",
            "Import stills, a video, or a .vlt project to start compositing.",
            self,
        )
        self.drop_overlay = QFrame(self)
        self.drop_overlay.setObjectName("dropOverlay")
        self.drop_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.drop_overlay.hide()
        self.hud = ZoomHud(self)
        self.hud.hide()

        self.view.zoom_changed.connect(self._on_zoom)
        self.view.files_dropped.connect(self.files_dropped.emit)
        self.view.drop_hover_changed.connect(self._on_drop_hover)
        self.empty.files_dropped.connect(self.files_dropped.emit)
        self.empty.drop_hover_changed.connect(self._on_drop_hover)
        self.empty.import_clicked.connect(self.import_clicked.emit)
        self.hud.fit_clicked.connect(lambda: self.view.fit_to_view(emit=True))
        self.hud.actual_clicked.connect(self.view.zoom_to_actual)
        self.hud.full_clicked.connect(self.full_clicked.emit)

    def set_preview(self, image: np.ndarray | None, *, fit: bool = False) -> None:
        """Update the displayed composite (or clear if None)."""
        self.view.set_preview(image, fit=fit)
        has = image is not None
        self.empty.setVisible(not has)
        self.hud.setVisible(has)
        if has:
            self.hud.set_zoom(self.view.current_zoom(), fit=self.view.is_fit_mode())
        self._layout_overlays()

    def set_import_enabled(self, enabled: bool) -> None:
        """Enable or disable the empty-state Import button."""
        self.empty.set_import_enabled(enabled)

    def is_fit_mode(self) -> bool:
        """True when the viewport is keeping the full image visible."""
        return self.view.is_fit_mode()

    def set_zoom(self, zoom: float) -> None:
        """Set absolute zoom factor from external state (exits fit mode)."""
        self.view.set_zoom(zoom)
        self.hud.set_zoom(self.view.current_zoom(), fit=False)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.view.setGeometry(self.rect())
        self._layout_overlays()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.view.setGeometry(self.rect())
        self._layout_overlays()

    def _layout_overlays(self) -> None:
        self.empty.setGeometry(self.rect())
        self.drop_overlay.setGeometry(self.rect().adjusted(16, 16, -16, -16))
        hint = self.hud.sizeHint()
        self.hud.resize(hint)
        self.hud.move(
            (self.width() - hint.width()) // 2,
            self.height() - hint.height() - 16,
        )
        self.empty.raise_()
        self.hud.raise_()
        self.drop_overlay.raise_()

    def _on_zoom(self, zoom: float) -> None:
        self.hud.set_zoom(zoom, fit=self.view.is_fit_mode())
        self.zoom_changed.emit(zoom)

    def _on_drop_hover(self, active: bool) -> None:
        self.drop_overlay.setVisible(active)
        if active:
            self.drop_overlay.raise_()
