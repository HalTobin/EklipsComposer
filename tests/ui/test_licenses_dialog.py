import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from eclipse_compositor.ui.widgets.about_dialog import LicensesDialog


def test_licenses_dialog_creates_and_exposes_dialog():
    app = QApplication.instance() or QApplication([])

    dialog = LicensesDialog()
    assert dialog.windowTitle() == "Licenses"
    assert "EklipsComposer" in dialog._license_text
    assert dialog.isModal()
    assert app is not None
