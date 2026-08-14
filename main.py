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


def main() -> int:
    """Launch the PySide6 MVI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("VulturEklips")
    app.setApplicationDisplayName("VulturEklips")
    app.setOrganizationName("VulturEklips")
    app.setDesktopFileName("VulturEklips")

    icon_file = app_icon_path()
    if icon_file.is_file():
        app.setWindowIcon(QIcon(str(icon_file)))

    view_model = ScreenViewModel()
    window = ScreenView(view_model)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
