"""Top header bar for the gallery: Title, count badge, Import action, and batch menu."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QWidget,
)

from eclipse_compositor.resources import icon_path
from eclipse_compositor.ui.theme import COLOR, ActionButton, qicon_from_path


class GalleryVisibilityButton(QPushButton):
    """Compact icon button for expanding or collapsing the project gallery."""

    def __init__(self, icon_name: str, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setIcon(qicon_from_path(icon_path(icon_name), size=16))
        self.setIconSize(QSize(16, 16))
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLOR.bg_sunken};
                color: {COLOR.text_muted};
                border: 1px solid {COLOR.border};
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {COLOR.bg_hover};
                color: {COLOR.text};
                border-color: {COLOR.border_strong};
            }}
            QPushButton:pressed {{ background: {COLOR.bg_sunken}; }}
            """
        )


class GalleryHeader(QWidget):
    """Clean, high-contrast header with section title, count badge, import button, and overflow menu."""

    import_clicked = Signal()
    select_all_clicked = Signal()
    unselect_all_clicked = Signal()
    toggle_favorite_clicked = Signal()
    remove_selected_clicked = Signal()
    collapse_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("PROJECT MEDIA")
        title.setStyleSheet(
            f"color: {COLOR.text_muted}; font-size: 11px; font-weight: 600;"
        )

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
        self.import_btn.setFixedHeight(28)
        self.import_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLOR.accent};
                color: {COLOR.accent_text};
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 0 10px;
                min-height: 28px;
                max-height: 28px;
                height: 28px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLOR.accent_hover};
            }}
            QPushButton:pressed {{
                background: {COLOR.accent_pressed};
            }}
            QPushButton:disabled {{
                background: {COLOR.border_strong};
                color: {COLOR.text_faint};
            }}
            """
        )

        self.more_btn = QPushButton("⋯")
        self.more_btn.setToolTip("Batch and selection actions")
        self.more_btn.setFixedSize(28, 28)
        self.more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLOR.bg_sunken};
                color: {COLOR.text_muted};
                border: 1px solid {COLOR.border};
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
                min-width: 28px;
                max-width: 28px;
                width: 28px;
                min-height: 28px;
                max-height: 28px;
                height: 28px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {COLOR.bg_hover};
                color: {COLOR.text};
                border-color: {COLOR.border_strong};
            }}
            QPushButton:pressed {{
                background: {COLOR.bg_sunken};
            }}
            QPushButton::menu-indicator {{
                image: none;
                width: 0px;
            }}
            """
        )

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

        self.more_btn.clicked.connect(self._show_more_menu)
        self.import_btn.clicked.connect(self.import_clicked.emit)
        self.collapse_btn = GalleryVisibilityButton("minus.svg", "Hide project gallery")
        self.collapse_btn.clicked.connect(self.collapse_clicked.emit)

        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._count_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)
        layout.addWidget(self.import_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.more_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.collapse_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def _show_more_menu(self) -> None:
        pos = self.more_btn.mapToGlobal(QPoint(0, self.more_btn.height() + 2))
        self._menu.exec(pos)

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
