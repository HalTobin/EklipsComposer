"""Interactive frame list widget with custom delegate rendering, drag-and-drop, and shortcuts."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QWidget,
)

from eclipse_compositor.cv.loading import load_image_bgr
from eclipse_compositor.ui.drop_import import mime_has_importable_paths, paths_from_mime
from eclipse_compositor.ui.state import GalleryViewMode, ImageItem
from eclipse_compositor.ui.theme import COLOR
from eclipse_compositor.ui.widgets.gallery.delegate import GalleryItemDelegate
from eclipse_compositor.ui.widgets.gallery.index_map import DisplayIndexMap
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage

_ICON_THUMB_SIZE = 96


def _pixmap_from_thumb(path: str) -> QPixmap:
    """Decode a gallery thumbnail via Pillow → QImage (no Qt image plugins)."""
    try:
        bgr = load_image_bgr(path)
    except (OSError, FileNotFoundError, ValueError):
        return QPixmap()
    qimg = bgr_to_qimage(bgr)
    if qimg.isNull():
        return QPixmap()
    return QPixmap.fromImage(qimg)


class FrameListWidget(QListWidget):
    """List widget supporting internal reordering, OS drag-and-drop, and rich card delegate rendering."""

    files_dropped = Signal(object)  # tuple[Path, ...]
    item_toggled = Signal(int, bool)  # original_index, enabled
    row_selected = Signal(object)  # int | None (original_index)
    selection_state_changed = Signal(bool, bool)  # has_selection, has_current
    rows_reordered = Signal(object)  # tuple[tuple[Path, bool], ...]
    remove_requested = Signal(object)  # tuple[int, ...]
    toggle_favorite_requested = Signal(int, bool)  # original_index, new_state
    show_properties_requested = Signal()
    adjust_circle_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._updating = False
        self._canvas_mode = False
        self._index_map = DisplayIndexMap()
        self._items: tuple[ImageItem, ...] = ()

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragEnabled(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setMinimumWidth(180)
        self.setMouseTracking(True)
        self.setSpacing(2)

        # Attach custom card delegate
        self._delegate = GalleryItemDelegate(self)
        self.setItemDelegate(self._delegate)
        self._delegate.favorite_toggled.connect(self._on_delegate_favorite)
        self._delegate.enabled_toggled.connect(self._on_delegate_enabled)

        self.currentRowChanged.connect(self._on_current_row_changed)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.model().rowsMoved.connect(self._on_rows_moved)

    def set_canvas_mode(self, enabled: bool) -> None:
        """Configure the list for composition-only canvas frames."""
        self._canvas_mode = enabled
        self._delegate.set_show_enabled_control(not enabled)

    # ---- Delegate interaction handlers ----

    def _on_delegate_favorite(self, visible_row: int) -> None:
        original = self._index_map.to_original(visible_row)
        if original is not None and original < len(self._items):
            item = self._items[original]
            self.toggle_favorite_requested.emit(original, not item.favorite)

    def _on_delegate_enabled(self, visible_row: int) -> None:
        original = self._index_map.to_original(visible_row)
        if original is not None and original < len(self._items):
            item = self._items[original]
            self.item_toggled.emit(original, not item.enabled)

    # ---- Drag and drop for OS files ----

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if mime_has_importable_paths(event.mimeData()):
            paths = paths_from_mime(event.mimeData())
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            if paths:
                self.files_dropped.emit(tuple(paths))
            return
        super().dropEvent(event)
        if self._canvas_mode:
            self._on_rows_moved()

    # ---- Keyboard Shortcuts ----

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            rows = self.selected_original_indices()
            if not rows:
                current = self.current_original_index()
                if current is not None:
                    rows = (current,)
            if rows:
                self.remove_requested.emit(rows)
                event.accept()
                return
        if event.key() == Qt.Key.Key_F:
            current = self.current_original_index()
            if current is not None and current < len(self._items):
                item = self._items[current]
                self.toggle_favorite_requested.emit(current, not item.favorite)
                event.accept()
                return
        super().keyPressEvent(event)

    # ---- Index Mapping Helpers ----

    def current_original_index(self) -> int | None:
        """Original index of the currently active row."""
        return self._index_map.to_original(self.currentRow())

    def selected_original_indices(self) -> tuple[int, ...]:
        """Original indices of all currently selected rows."""
        visible_rows = [self.row(item) for item in self.selectedItems()]
        return self._index_map.selected_original_indices(visible_rows)

    # ---- List Events ----

    def _on_current_row_changed(self, row: int) -> None:
        if self._updating:
            return
        self._notify_selection_state()
        original = self._index_map.to_original(row)
        self.row_selected.emit(original)

    def _on_selection_changed(self) -> None:
        if self._updating:
            return
        self._notify_selection_state()

    def _notify_selection_state(self) -> None:
        has_selection = bool(self.selectedItems())
        has_current = self.currentRow() >= 0
        self.selection_state_changed.emit(has_selection, has_current)

    def _on_rows_moved(self, *_args: object) -> None:
        if self._updating:
            return
        rows_data: list[tuple[Path, bool]] = []
        for visible in range(self.count()):
            row_item = self.item(visible)
            item_data = row_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(item_data, ImageItem):
                rows_data.append((item_data.path, item_data.enabled))
            else:
                path = item_data if isinstance(item_data, Path) else Path(str(item_data))
                rows_data.append((path, True))
        self.rows_reordered.emit(tuple(rows_data))

    def _on_context_menu(self, pos) -> None:
        item_at_pos = self.itemAt(pos)
        if item_at_pos is None:
            return
        visible_row = self.row(item_at_pos)
        original = self._index_map.to_original(visible_row)
        if original is None or original >= len(self._items):
            return

        if visible_row not in {self.row(it) for it in self.selectedItems()}:
            self.clearSelection()
            self.setCurrentRow(visible_row)

        if self._canvas_mode:
            menu = QMenu(self)
            remove_action = menu.addAction("Remove from canvas")
            remove_action.triggered.connect(self._on_context_remove)
            menu.exec(self.viewport().mapToGlobal(pos))
            return

        item = self._items[original]
        menu = QMenu(self)
        fav_text = "Unfavorite" if item.favorite else "Favorite"
        fav_action = menu.addAction(fav_text)
        fav_action.triggered.connect(
            lambda: self.toggle_favorite_requested.emit(original, not item.favorite)
        )
        menu.addSeparator()
        props_action = menu.addAction("Properties")
        props_action.triggered.connect(self.show_properties_requested.emit)
        adjust_action = menu.addAction("Adjust circle")
        adjust_action.triggered.connect(lambda: self.adjust_circle_requested.emit(original))
        menu.addSeparator()
        remove_action = menu.addAction("Remove")
        remove_action.triggered.connect(self._on_context_remove)

        menu.exec(self.viewport().mapToGlobal(pos))

    def _on_context_remove(self) -> None:
        rows = self.selected_original_indices()
        if not rows:
            current = self.current_original_index()
            if current is not None:
                rows = (current,)
        if rows:
            self.remove_requested.emit(rows)

    # ---- Mode Configuration ----

    def configure_for_mode(self, mode: GalleryViewMode, can_reorder: bool) -> None:
        """Configure layout, flow, icon sizes, and stylesheet for the given view mode."""
        self.setDragEnabled(can_reorder)
        self._delegate.set_view_mode(mode)

        if mode == GalleryViewMode.ICON:
            self.setViewMode(QListWidget.ViewMode.IconMode)
            self.setFlow(QListWidget.Flow.LeftToRight)
            self.setWrapping(True)
            self.setGridSize(QSize(96, 114))
            self.setSpacing(4)
            self.setStyleSheet(
                f"QListWidget {{ background: {COLOR.bg_sunken}; border: 1px solid {COLOR.border}; border-radius: 8px; padding: 4px; outline: none; }}"
            )
        elif mode == GalleryViewMode.LIST_SIMPLE:
            self.setViewMode(QListWidget.ViewMode.ListMode)
            self.setFlow(QListWidget.Flow.TopToBottom)
            self.setWrapping(False)
            self.setGridSize(QSize())
            self.setSpacing(2)
            self.setStyleSheet(
                f"QListWidget {{ background: {COLOR.bg_sunken}; border: 1px solid {COLOR.border}; border-radius: 8px; padding: 3px; outline: none; }}"
            )
        else:
            self.setViewMode(QListWidget.ViewMode.ListMode)
            self.setFlow(QListWidget.Flow.TopToBottom)
            self.setWrapping(False)
            self.setGridSize(QSize())
            self.setSpacing(3)
            self.setStyleSheet(
                f"QListWidget {{ background: {COLOR.bg_sunken}; border: 1px solid {COLOR.border}; border-radius: 8px; padding: 3px; outline: none; }}"
            )

    # ---- Populate List ----

    def populate(
        self,
        items: tuple[ImageItem, ...],
        index_map: DisplayIndexMap,
        view_mode: GalleryViewMode,
        selected_index: int | None,
    ) -> None:
        """Synchronize the list widget items with current image items and index map."""
        self._items = items
        self._index_map = index_map
        self.configure_for_mode(view_mode, index_map.can_reorder)

        self._updating = True
        try:
            current_visible = index_map.to_visible(selected_index)
            self.clear()
            for visible_row, original_idx in enumerate(index_map.display_indices):
                item = items[original_idx]
                row = QListWidgetItem()
                row.setData(Qt.ItemDataRole.UserRole, item)
                row.setSizeHint(self._delegate.item_size_hint(view_mode))
                row.setFlags(
                    row.flags()
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsDragEnabled
                    | Qt.ItemFlag.ItemIsDropEnabled
                )
                self.addItem(row)

            if current_visible is not None:
                self.setCurrentRow(current_visible)
        finally:
            self._updating = False

        self._notify_selection_state()
