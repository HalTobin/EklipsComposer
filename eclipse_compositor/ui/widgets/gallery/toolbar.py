"""Secondary toolbar for the gallery: View modes, Sort dropdown, and Favorites filter chip."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
)

from eclipse_compositor.resources import icon_path
from eclipse_compositor.ui.state import GallerySortMode, GalleryViewMode
from eclipse_compositor.ui.theme import COLOR, ActionButton, ComboField, SegmentedControl, qicon_from_path


def _view_mode_icon(filename: str) -> QIcon | None:
    """Load an SVG icon from ``assets/icons/``; return None for text fallback."""
    path = icon_path(filename)
    if not path.is_file():
        return None
    icon = qicon_from_path(path, size=18)
    return icon if not icon.isNull() else None


class GalleryToolbar(QWidget):
    """Compact toolbar containing view mode toggles, sorting selector, and favorite filter chip."""

    view_mode_changed = Signal(object)  # GalleryViewMode
    sort_mode_changed = Signal(object)  # GallerySortMode
    show_only_favorites_changed = Signal(bool)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        include_icon_mode: bool = True,
    ) -> None:
        super().__init__(parent)
        self._updating = False
        self._include_icon_mode = include_icon_mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        modes = ["Preview", "List"]
        icons = [_view_mode_icon("rows.svg"), _view_mode_icon("list.svg")]
        tooltips = ["Preview list with thumbnails", "Compact list"]
        if include_icon_mode:
            modes.append("Icons")
            icons.append(_view_mode_icon("grid.svg"))
            tooltips.append("Icon grid")

        self.view_mode = SegmentedControl(
            modes,
            icons=icons,
            tooltips=tooltips,
            compact=True,
        )
        self.view_mode.setToolTip("Frame list appearance")

        self.sort_mode = ComboField(
            "",
            [
                ("Title", GallerySortMode.TITLE),
                ("Date taken", GallerySortMode.DATE_TAKEN),
            ],
        )
        self.sort_mode.setToolTip("Order frames by filename or EXIF capture time")

        self.favorites_btn = ActionButton("★ Favorites", variant="ghost")
        self.favorites_btn.setCheckable(True)
        self.favorites_btn.setToolTip("Show only favorite frames and current selection")
        self.favorites_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_filter_style(False)

        layout.addWidget(self.view_mode)
        layout.addWidget(self.sort_mode, stretch=1)
        layout.addWidget(self.favorites_btn)

        self.view_mode.currentChanged.connect(self._on_view_mode_index)
        self.sort_mode.currentDataChanged.connect(self.sort_mode_changed.emit)
        self.favorites_btn.toggled.connect(self._on_favorites_toggled)

    def _update_filter_style(self, checked: bool) -> None:
        if checked:
            self.favorites_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {COLOR.accent_soft};
                    color: {COLOR.accent};
                    border: 1px solid {COLOR.accent};
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-weight: 600;
                    font-size: 11px;
                }}
                """
            )
        else:
            self.favorites_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {COLOR.bg_sunken};
                    color: {COLOR.text_muted};
                    border: 1px solid {COLOR.border};
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {COLOR.bg_hover};
                    color: {COLOR.text};
                    border-color: {COLOR.border_strong};
                }}
                """
            )

    def _on_view_mode_index(self, index: int) -> None:
        if self._updating:
            return
        mode = GalleryViewMode.LIST_PREVIEW
        if index == 1:
            mode = GalleryViewMode.LIST_SIMPLE
        elif self._include_icon_mode and index == 2:
            mode = GalleryViewMode.ICON
        self.view_mode_changed.emit(mode)

    def _on_favorites_toggled(self, checked: bool) -> None:
        self._update_filter_style(checked)
        if self._updating:
            return
        self.show_only_favorites_changed.emit(checked)

    def sync(
        self,
        view_mode: GalleryViewMode,
        sort_mode: GallerySortMode,
        show_only_favorites: bool,
    ) -> None:
        """Update toolbar widgets without re-emitting signals."""
        self._updating = True
        try:
            if view_mode == GalleryViewMode.LIST_SIMPLE:
                self.view_mode.setCurrentIndex(1)
            elif view_mode == GalleryViewMode.ICON and self._include_icon_mode:
                self.view_mode.setCurrentIndex(2)
            else:
                self.view_mode.setCurrentIndex(0)

            self.sort_mode.setCurrentData(sort_mode)
            if self.favorites_btn.isChecked() != show_only_favorites:
                self.favorites_btn.setChecked(show_only_favorites)
                self._update_filter_style(show_only_favorites)
        finally:
            self._updating = False
