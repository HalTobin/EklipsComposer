#!/usr/bin/env python3
"""EklipsComposer entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, Signal
from PySide6.QtGui import QFileOpenEvent
from PySide6.QtWidgets import QApplication

from eclipse_compositor import APP_NAME, __version__
from eclipse_compositor.project import is_project_file
from eclipse_compositor.resources import app_icon_path
from eclipse_compositor.ui.theme import apply_theme, qicon_from_path
from eclipse_compositor.ui.view import ScreenView
from eclipse_compositor.ui.viewmodel import ScreenViewModel


class EklipsComposerApplication(QApplication):
    """QApplication that turns macOS Finder / argv file opens into a signal.

    Double-clicking a ``.vlt`` sends a ``QFileOpenEvent`` (often *before* the
    main window exists). Paths are buffered until ``set_window_ready``.
    Keep PyInstaller ``argv_emulation`` off so Qt still receives these events.
    """

    file_open_requested = Signal(str)

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self._window_ready = False
        self._pending_paths: list[str] = []

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FileOpen and isinstance(event, QFileOpenEvent):
            self.offer_path(event.file())
            return True
        return super().event(event)

    def offer_path(self, path: str) -> None:
        """Queue or emit *path* if it is a EklipsComposer project file."""
        if not path or not is_project_file(path):
            return
        if not self._window_ready:
            self._pending_paths.append(path)
            return
        self.file_open_requested.emit(path)

    def set_window_ready(self) -> None:
        """Flush buffered opens now that the main window can handle them."""
        self._window_ready = True
        pending = self._pending_paths
        self._pending_paths = []
        if not pending:
            return
        # One project at launch; later FileOpen events emit immediately.
        self.file_open_requested.emit(pending[-1])


def _macos_set_app_menu_name(name: str) -> None:
    """Set the macOS application menu title (otherwise 'Python').

    Cocoa reads ``CFBundleName`` from the running process Info.plist. When
    launched via the interpreter that value is "Python", so Qt names the
    application menu (About / Hide / Quit) accordingly. Mutating the
    in-memory dictionary *before* ``QApplication`` is constructed makes Qt
    pick up our name instead. Packaged ``.app`` bundles already set this in
    Info.plist; this is a no-op in that case.
    """
    if sys.platform != "darwin":
        return
    try:
        from ctypes import c_char_p, c_void_p, cdll, util

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

        def _nsstring(text: str) -> int:
            return _msg(
                c_void_p,
                objc.objc_getClass(b"NSString"),
                objc.sel_registerName(b"stringWithUTF8String:"),
                text.encode("utf-8"),
                argtypes=(c_char_p,),
            )

        bundle = _msg(
            c_void_p,
            objc.objc_getClass(b"NSBundle"),
            objc.sel_registerName(b"mainBundle"),
        )
        if not bundle:
            return
        info = _msg(c_void_p, bundle, objc.sel_registerName(b"infoDictionary"))
        if not info:
            return
        set_object = objc.sel_registerName(b"setObject:forKey:")
        ns_name = _nsstring(name)
        for key in ("CFBundleName", "CFBundleDisplayName"):
            _msg(
                None,
                info,
                set_object,
                ns_name,
                _nsstring(key),
                argtypes=(c_void_p, c_void_p),
            )
    except Exception:
        logging.getLogger(__name__).debug(
            "Could not set macOS application menu name",
            exc_info=True,
        )


def _project_path_from_argv(argv: list[str]) -> Path | None:
    """Return the last ``.vlt`` path passed on the command line, if any."""
    found: Path | None = None
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        path = Path(arg)
        if is_project_file(path) and path.is_file():
            found = path
    return found


def main() -> int:
    """Launch the PySide6 MVI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    _macos_set_app_menu_name(APP_NAME)
    app = EklipsComposerApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_NAME)
    app.setDesktopFileName(APP_NAME)

    icon = qicon_from_path(app_icon_path())
    if not icon.isNull():
        app.setWindowIcon(icon)
    apply_theme(app)

    view_model = ScreenViewModel()
    window = ScreenView(view_model)
    app.file_open_requested.connect(window.open_project_from_os)
    window.show()

    argv_project = _project_path_from_argv(sys.argv)
    if argv_project is not None:
        app.offer_path(str(argv_project))
    app.set_window_ready()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
