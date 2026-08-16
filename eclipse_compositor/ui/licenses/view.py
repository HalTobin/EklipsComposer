"""Licenses dialog: scrollable dependency list with a scrollable detail pane."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QScrollArea,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.licenses.state import LicensesState, selected_dependency
from eclipse_compositor.ui.licenses.viewmodel import LicensesViewModel
from eclipse_compositor.ui.theme import COLOR, SPACE


class LicensesDialog(QDialog):
    """Renders ``LicensesState`` from a ``LicensesViewModel``."""

    def __init__(
        self,
        parent: QWidget | None = None,
        view_model: LicensesViewModel | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("licensesDialog")
        self.setWindowTitle("Licenses")
        self.setModal(True)
        self.setMinimumSize(760, 480)

        self.view_model = view_model or LicensesViewModel()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.xl, SPACE.xl, SPACE.xl, SPACE.lg)
        layout.setSpacing(SPACE.md)

        title = QLabel("Open-source licenses")
        title.setObjectName("aboutAppName")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list = QListWidget()
        self._list.setObjectName("licensesDependencyList")
        self._list.currentRowChanged.connect(self._on_row_changed)
        splitter.addWidget(self._list)

        self._name_label = QLabel()
        self._name_label.setObjectName("aboutAppName")
        self._developer_label = QLabel()
        self._developer_label.setObjectName("aboutMeta")
        self._repo_label = QLabel()
        self._repo_label.setObjectName("aboutLink")
        self._repo_label.setOpenExternalLinks(True)
        self._repo_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self._license_text = QTextBrowser()
        self._license_text.setReadOnly(True)
        self._license_text.setOpenExternalLinks(True)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(SPACE.md, 0, 0, 0)
        detail_layout.setSpacing(SPACE.sm)
        detail_layout.addWidget(self._name_label)
        detail_layout.addWidget(self._developer_label)
        detail_layout.addWidget(self._repo_label)
        detail_layout.addWidget(self._license_text, stretch=1)

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setWidget(detail)
        splitter.addWidget(detail_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.view_model.state_changed.connect(self._render)
        self.view_model.load()

    def _on_row_changed(self, index: int) -> None:
        if index < 0:
            return
        self.view_model.select_dependency(index)

    def _render(self, state: LicensesState) -> None:
        if self._list.count() != len(state.dependencies):
            self._list.blockSignals(True)
            self._list.clear()
            self._list.addItems([dep.name for dep in state.dependencies])
            self._list.blockSignals(False)

        if state.selected_index is not None and self._list.currentRow() != state.selected_index:
            self._list.blockSignals(True)
            self._list.setCurrentRow(state.selected_index)
            self._list.blockSignals(False)

        dependency = selected_dependency(state)
        if dependency is None:
            self._name_label.setText("")
            self._developer_label.setText("")
            self._repo_label.setText("")
            self._license_text.setPlainText(state.error_message or "")
            return

        self._name_label.setText(dependency.name)
        self._developer_label.setText(f"Developed by {dependency.developer}")
        self._repo_label.setText(
            f'<a href="{dependency.repository_url}" style="color: {COLOR.accent};">'
            f"{dependency.repository_url}</a>"
        )
        sections = [
            f"{license.name}\n{'-' * len(license.name)}\n{license.text}"
            for license in dependency.licenses
        ]
        self._license_text.setPlainText("\n\n".join(sections))


def show_licenses_dialog(parent: QWidget | None = None) -> None:
    """Open the Licenses dialog modally."""
    dialog = LicensesDialog(parent)
    dialog.exec()
