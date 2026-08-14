#!/usr/bin/env python3
"""VulturEklips entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from eclipse_compositor.resources import app_icon_path
from eclipse_compositor.ui.view import ScreenView
from eclipse_compositor.ui.viewmodel import ScreenViewModel

_APP_NAME = "VulturEklips"


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


def main() -> int:
    """Launch the PySide6 MVI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    _macos_set_app_menu_name(_APP_NAME)
    app = QApplication(sys.argv)
    app.setApplicationName(_APP_NAME)
    app.setApplicationDisplayName(_APP_NAME)
    app.setOrganizationName(_APP_NAME)
    app.setDesktopFileName(_APP_NAME)

    icon_file = app_icon_path()
    if icon_file.is_file():
        app.setWindowIcon(QIcon(str(icon_file)))

    view_model = ScreenViewModel()
    window = ScreenView(view_model)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
