"""About dialog: app name, version, developer, and repository link."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor import APP_NAME, GITHUB_URL, __author__, __version__
from eclipse_compositor.resources import app_mark_path
from eclipse_compositor.ui.licenses import show_licenses_dialog
from eclipse_compositor.ui.theme import COLOR, SPACE, EclipseMark, qicon_from_path


class AboutDialog(QDialog):
    """Credits and version for EklipsComposer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.xl, SPACE.xl, SPACE.xl, SPACE.lg)
        layout.setSpacing(SPACE.sm)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        icon = qicon_from_path(app_mark_path(), size=96)
        if not icon.isNull():
            mark = QLabel()
            mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mark.setPixmap(icon.pixmap(96, 96))
            layout.addWidget(mark, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            layout.addWidget(EclipseMark(size=96), alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(APP_NAME)
        title.setObjectName("aboutAppName")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel(f"Version {__version__}")
        version.setObjectName("aboutMeta")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        developer = QLabel(f"Developed by {__author__}")
        developer.setObjectName("aboutMeta")
        developer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(developer)

        repo = QLabel(
            f'<a href="{GITHUB_URL}" style="color: {COLOR.accent};">'
            f"{GITHUB_URL.removeprefix('https://')}</a>"
        )
        repo.setObjectName("aboutLink")
        repo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        repo.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        repo.setOpenExternalLinks(True)
        layout.addWidget(repo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        licenses = buttons.addButton("Licenses", QDialogButtonBox.ButtonRole.ActionRole)
        licenses.clicked.connect(self._show_licenses)
        buttons.rejected.connect(self.reject)
        layout.addSpacing(SPACE.md)
        layout.addWidget(buttons)

    def _show_licenses(self) -> None:
        show_licenses_dialog(self)


def show_about_dialog(parent: QWidget | None = None) -> None:
    """Open the About dialog modally."""
    dialog = AboutDialog(parent)
    dialog.exec()
