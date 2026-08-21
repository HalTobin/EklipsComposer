"""Top header bar for the gallery: Title, count badge, Import action, and batch menu."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QWidget,
)

from eclipse_compositor.ui.theme import COLOR, ActionButton, FieldLabel


class GalleryHeader(QWidget):
    """Clean, high-contrast header with section title, count badge, import button, and overflow menu."""

    import_clicked = Signal()
    select_all_clicked = Signal()
    unselect_all_clicked = Signal()
    toggle_favorite_clicked = Signal()
    remove_selected_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = FieldLabel("FRAMES")

        # Pill badge for frame & favorite counts
        self._count_badge = QLabel()
        self._count_badge.setStyleSheet(
            f"""
            QLabel {{
                background: {COLOR.bg_raised};
                color: {COLOR.text_muted};
                border: 1px solid {COLOR.border};
                border-radius: 9px;
                padding: 1px 7px;
                font-size: 11px;
                font-weight: 600;
            }}
            """
        )
        self._count_badge.hide()

        self.import_btn = ActionButton("+ Import", variant="primary")
        self.import_btn.setToolTip("Import images or video into the gallery")

        self.more_btn = ActionButton("⋯", variant="ghost")
        self.more_btn.setToolTip("Batch and selection actions")
        self.more_btn.setFixedSize(28, 28)

        self._menu = QMenu(self)
        self._select_all_action = self._menu.addAction("Enable All Frames")
        self._unselect_all_action = self._menu.addAction("Disable All Frames")
        self._menu.addSeparator()
        self._favorite_action = self._menu.addAction("Toggle Favorite")
        self._remove_action = self._menu.addAction("Remove Selected")

        self._select_all_action.triggered.connect(self.select_all_clicked.emit)
        self._unselect_all_action.triggered.connect(self.unselect_all_clicked.emit)
        self._favorite_action.triggered.connect(self.toggle_favorite_clicked.emit)
        self._remove_action.triggered.connect(self.remove_selected_clicked.emit)

        self.more_btn.setMenu(self._menu)
        self.import_btn.clicked.connect(self.import_clicked.emit)

        layout.addWidget(title)
        layout.addWidget(self._count_badge)
        layout.addStretch(1)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.more_btn)

    def set_counts(self, enabled: int, total: int, favorites: int) -> None:
        """Update the count badge next to the section title."""
        if total == 0:
            self._count_badge.hide()
            return

        fav_suffix = f" · <span style='color: {COLOR.accent};'>★ {favorites}</span>" if favorites else ""
        if enabled == total:
            self._count_badge.setText(f"{total}{fav_suffix}")
        else:
            self._count_badge.setText(f"{enabled}/{total}{fav_suffix}")
        self._count_badge.show()

    def set_import_enabled(self, enabled: bool) -> None:
        """Enable or disable the Import action button."""
        self.import_btn.setEnabled(enabled)

    def set_selection_actions_enabled(self, has_selection: bool, has_items: bool) -> None:
        """Enable or disable actions in the batch menu."""
        self._select_all_action.setEnabled(has_items)
        self._unselect_all_action.setEnabled(has_items)
        self._favorite_action.setEnabled(has_selection)
        self._remove_action.setEnabled(has_selection)
