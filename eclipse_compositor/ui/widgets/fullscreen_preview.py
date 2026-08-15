"""Maximized preview window for the current composite.

On macOS, ``showFullScreen()`` creates a new Space and a frameless window
loses the traffic lights. This viewer is a normal window sized to the
current screen's available geometry instead.
"""

from __future__ import annotations

import logging
import sys
from ctypes import c_char_p, c_ulong, c_void_p, cdll, util

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QResizeEvent, QScreen, QShowEvent
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from eclipse_compositor.ui.theme import CaptionLabel, ZoomHud
from eclipse_compositor.ui.widgets.viewport import PreviewViewport

_NS_MOVE_TO_ACTIVE_SPACE = 1 << 1
_NS_FULL_SCREEN_NONE = 1 << 9


def _macos_keep_on_current_space(widget: QWidget) -> None:
    """Prevent Cocoa from promoting *widget* into a separate fullscreen Space."""
    if sys.platform != "darwin":
        return
    if QApplication.platformName() != "cocoa":
        return
    try:
        widget.winId()
        lib_path = util.find_library("objc")
        if lib_path is None:
            return
        objc = cdll.LoadLibrary(lib_path)
        objc.objc_getClass.restype = c_void_p
        objc.objc_getClass.argtypes = [c_char_p]
        objc.sel_registerName.restype = c_void_p
        objc.sel_registerName.argtypes = [c_char_p]

        def _msg(restype, receiver, selector, *args, argtypes=()):
            objc.objc_msgSend.restype = restype
            objc.objc_msgSend.argtypes = [c_void_p, c_void_p, *argtypes]
            return objc.objc_msgSend(receiver, selector, *args)

        nsview = c_void_p(int(widget.winId()))
        if not nsview.value:
            return
        nswindow = _msg(
            c_void_p, nsview, objc.sel_registerName(b"window")
        )
        if not nswindow:
            return
        _msg(
            None,
            nswindow,
            objc.sel_registerName(b"setCollectionBehavior:"),
            _NS_MOVE_TO_ACTIVE_SPACE | _NS_FULL_SCREEN_NONE,
            argtypes=(c_ulong,),
        )
    except Exception:
        logging.getLogger(__name__).debug(
            "Could not disable macOS native fullscreen Spaces",
            exc_info=True,
        )


class FullscreenPreview(QWidget):
    """Normal window that fills the current screen, with OS close/hide/zoom."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setObjectName("fullscreenPreview")
        self.setWindowTitle("Composite preview")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Explicit traffic lights; omit WindowFullscreenButtonHint so the
        # green button zooms instead of creating a macOS fullscreen Space.
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowFlag(Qt.WindowType.WindowFullscreenButtonHint, False)

        self._view = PreviewViewport(self)
        self._view.setAcceptDrops(False)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._view)

        self._hud = ZoomHud(self, show_full=False)
        self._hud.hide()
        self._hud.fit_clicked.connect(lambda: self._view.fit_to_view(emit=False))
        self._hud.actual_clicked.connect(self._view.zoom_to_actual)
        self._view.zoom_changed.connect(self._on_zoom)

        self._hint = CaptionLabel(
            "Esc to close  ·  scroll to zoom  ·  double-click to fit"
        )
        self._hint.setParent(self)
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_preview(self, image: np.ndarray | None, *, fit: bool = True) -> None:
        """Replace the displayed composite (or clear if None)."""
        self._view.set_preview(image, fit=fit)
        has = image is not None
        self._hud.setVisible(has)
        self._hint.setVisible(has)
        if has:
            self._hud.set_zoom(self._view.current_zoom(), fit=self._view.is_fit_mode())
        self._layout_chrome()

    def present(self) -> None:
        """Show this window filling the parent window's current screen."""
        screen = self._screen_for_parent()
        if screen is not None:
            self.setGeometry(screen.availableGeometry())
        self.show()
        self.setWindowState(
            (self.windowState() & ~Qt.WindowState.WindowMinimized)
            | Qt.WindowState.WindowActive
        )
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        _macos_keep_on_current_space(self)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        _macos_keep_on_current_space(self)
        if self._view.has_preview():
            self._view.fit_to_view(emit=False)
            self._hud.set_zoom(self._view.current_zoom(), fit=True)
        self._layout_chrome()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._layout_chrome()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def _screen_for_parent(self) -> QScreen | None:
        parent = self.parentWidget()
        if parent is not None:
            screen = parent.screen()
            if screen is not None:
                return screen
        handle = self.windowHandle()
        if handle is not None:
            return handle.screen()
        return QApplication.primaryScreen()

    def _on_zoom(self, zoom: float) -> None:
        self._hud.set_zoom(zoom, fit=self._view.is_fit_mode())

    def _layout_chrome(self) -> None:
        hint = self._hud.sizeHint()
        self._hud.resize(hint)
        self._hud.move(
            (self.width() - hint.width()) // 2,
            self.height() - hint.height() - 36,
        )
        self._hud.raise_()
        self._hint.adjustSize()
        self._hint.move(
            (self.width() - self._hint.width()) // 2,
            self.height() - self._hint.height() - 14,
        )
        self._hint.raise_()
