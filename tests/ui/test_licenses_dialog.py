import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from eclipse_compositor.ui.licenses import LicensesDialog
from eclipse_compositor.ui.licenses.state import selected_dependency


def test_licenses_dialog_loads_and_renders_dependencies():
    app = QApplication.instance() or QApplication([])

    dialog = LicensesDialog()
    assert dialog.windowTitle() == "Licenses"
    assert dialog.isModal()

    state = dialog.view_model.state
    assert state.dependencies
    assert dialog._list.count() == len(state.dependencies)

    dependency = selected_dependency(state)
    assert dependency is not None
    assert dialog._name_label.text() == dependency.name
    assert app is not None
