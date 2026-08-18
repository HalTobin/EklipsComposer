"""Frame list with enable checkboxes, favorites, sorting, and view modes."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.loading import load_image_bgr
from eclipse_compositor.ui.drop_import import mime_has_importable_paths, paths_from_mime
from eclipse_compositor.ui.state import GallerySortMode, GalleryViewMode, ImageItem, JobStatus, ScreenState
from eclipse_compositor.ui.theme import COLOR, ActionButton, CaptionLabel, ComboField, HintLabel, SegmentedControl, ToggleRow
from eclipse_compositor.ui.widgets.frame_preview import FramePreview
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage

_THUMB_SIZE = 48
_ICON_THUMB_SIZE = 80
_STAR_ON = "★"
_STAR_OFF = "☆"


_LIST_PREVIEW_QSS = """
QListWidget { padding: 2px; }
QListWidget::item { padding: 2px 6px; min-height: 40px; border-radius: 4px; }
"""

_LIST_SIMPLE_QSS = """
QListWidget { padding: 1px; }
QListWidget::item { padding: 1px 6px; min-height: 26px; border-radius: 4px; }
"""

_ICON_QSS = """
QListWidget { padding: 4px; }
QListWidget::item { padding: 4px; border-radius: 4px; }
"""


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
    """Gallery list that reorders internally and accepts dropped image files."""

    files_dropped = Signal(object)  # tuple[Path, ...]

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


class GalleryBar(QWidget):
    """Side panel: draggable frame list with per-frame enable toggles."""

    toggle_image = Signal(int, bool)
    toggle_favorite = Signal(int, bool)
    select_image = Signal(object)  # int | None
    remove_clicked = Signal(object)  # int | None
    reorder_images = Signal(object)  # tuple[ImageItem, ...]
    files_dropped = Signal(object)  # tuple[Path, ...]
    import_clicked = Signal()
    view_mode_changed = Signal(object)  # GalleryViewMode
    sort_mode_changed = Signal(object)  # GallerySortMode
    show_only_favorites_changed = Signal(bool)
    select_all_clicked = Signal()
    unselect_all_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("gallery")
        self._updating = False
        self._items: tuple[ImageItem, ...] = ()
        self._icons: dict[str, QIcon] = {}
        self._display_indices: list[int] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(8)

        # ---- Toolbar row 1: import / remove / select all / favorite ----
        row_buttons = QHBoxLayout()
        row_buttons.setSpacing(6)
        self.import_btn = ActionButton("Import")
        self.remove_btn = ActionButton("Remove", variant="ghost")
        self.remove_btn.setEnabled(False)
        self.select_all_btn = ActionButton("All", variant="ghost")
        self.select_all_btn.setToolTip("Enable all frames in the composite")
        self.unselect_all_btn = ActionButton("None", variant="ghost")
        self.unselect_all_btn.setToolTip("Disable all frames")
        self.favorite_btn = ActionButton("☆", variant="ghost")
        self.favorite_btn.setToolTip("Toggle favorite for selected frame")
        self.favorite_btn.setEnabled(False)
        row_buttons.addWidget(self.import_btn)
        row_buttons.addWidget(self.remove_btn)
        row_buttons.addSpacing(8)
        row_buttons.addWidget(self.select_all_btn)
        row_buttons.addWidget(self.unselect_all_btn)
        row_buttons.addStretch(1)
        row_buttons.addWidget(self.favorite_btn)
        layout.addLayout(row_buttons)

        # ---- Toolbar row 2: view mode / sort / favorites filter ----
        row_tools = QHBoxLayout()
        row_tools.setSpacing(8)
        self.view_mode = SegmentedControl(["Preview", "List", "Icons"])
        self.view_mode.setToolTip("Frame list appearance")
        self.sort_mode = ComboField(
            "Sort by",
            [
                ("Title", GallerySortMode.TITLE),
                ("Date taken", GallerySortMode.DATE_TAKEN),
            ],
        )
        self.sort_mode.setToolTip("Order frames by filename or EXIF capture time")
        self.favorites_filter = ToggleRow("Favorites only")
        self.favorites_filter.setToolTip("Show only favorite frames and the current selection")
        row_tools.addWidget(self.view_mode, stretch=1)
        row_tools.addWidget(self.sort_mode)
        row_tools.addWidget(self.favorites_filter)
        layout.addLayout(row_tools)

        # ---- Header ----
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        title = CaptionLabel("Frames")
        title.setObjectName("sectionTitle")
        self._count = CaptionLabel()
        self._count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(title)
        header_row.addWidget(self._count, stretch=1)
        layout.addLayout(header_row)

        hint = HintLabel("Drag to reorder")
        self._hint = hint
        layout.addWidget(hint)

        self.list = FrameListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list.setDragEnabled(True)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentRowChanged.connect(self._on_row_changed)
        self.list.itemSelectionChanged.connect(self._on_selection_changed)
        self.list.customContextMenuRequested.connect(self._on_context_menu)
        self.list.model().rowsMoved.connect(self._on_rows_moved)
        self.list.files_dropped.connect(self.files_dropped.emit)
        self.list.setMinimumWidth(180)
        self.list.setIconSize(QSize(_THUMB_SIZE, _THUMB_SIZE))
        self.list.setSpacing(2)

        self.frame_preview = FramePreview()

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.list)
        split.addWidget(self.frame_preview)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        split.setSizes([520, 140])
        layout.addWidget(split)
        self.setMinimumWidth(220)

        self.import_btn.clicked.connect(self.import_clicked.emit)
        self.remove_btn.clicked.connect(self._on_remove_selected)
        self.select_all_btn.clicked.connect(self.select_all_clicked.emit)
        self.unselect_all_btn.clicked.connect(self.unselect_all_clicked.emit)
        self.favorite_btn.clicked.connect(self._on_favorite_selected)
        self.view_mode.currentChanged.connect(self._on_view_mode_changed)
        self.sort_mode.currentDataChanged.connect(self.sort_mode_changed.emit)
        self.favorites_filter.toggled.connect(self.show_only_favorites_changed.emit)

    # ---- Internal helpers ----

    def _original_index(self, visible_row: int) -> int | None:
        if 0 <= visible_row < len(self._display_indices):
            return self._display_indices[visible_row]
        return None

    def _visible_row(self, original_index: int) -> int | None:
        try:
            return self._display_indices.index(original_index)
        except ValueError:
            return None

    def _selected_original_indices(self) -> tuple[int, ...]:
        return tuple(
            idx
            for idx in (
                self._original_index(self.list.row(item))
                for item in self.list.selectedItems()
            )
            if idx is not None
        )

    def _current_original_index(self) -> int | None:
        return self._original_index(self.list.currentRow())

    def _on_remove_selected(self) -> None:
        rows = self._selected_original_indices()
        if not rows:
            row = self._current_original_index()
            if row is not None:
                rows = (row,)
            else:
                return
        self.remove_clicked.emit(rows)

    def _on_favorite_selected(self) -> None:
        index = self._current_original_index()
        if index is None:
            return
        item = self._items[index]
        self.toggle_favorite.emit(index, not item.favorite)

    def _on_item_changed(self, row_item: QListWidgetItem) -> None:
        if self._updating:
            return
        original = self._original_index(self.list.row(row_item))
        if original is None:
            return
        enabled = row_item.checkState() == Qt.CheckState.Checked
        self.toggle_image.emit(original, enabled)

    def _sync_favorite_button(self) -> None:
        original = self._current_original_index()
        if original is None:
            self.favorite_btn.setText("☆")
            return
        item = self._items[original]
        self.favorite_btn.setText("★" if item.favorite else "☆")

    def _on_selection_changed(self) -> None:
        has_selection = bool(self.list.selectedItems())
        self.remove_btn.setEnabled(has_selection or self.list.currentRow() >= 0)
        self.favorite_btn.setEnabled(self.list.currentRow() >= 0)
        self._sync_favorite_button()

    def _on_row_changed(self, row: int) -> None:
        if self._updating:
            return
        has_current = row >= 0
        self.remove_btn.setEnabled(has_current or bool(self.list.selectedItems()))
        self.favorite_btn.setEnabled(has_current)
        self._sync_favorite_button()
        original = self._original_index(row)
        self.select_image.emit(original)

    def _on_context_menu(self, pos) -> None:
        visible_row = self.list.row(self.list.itemAt(pos))
        original = self._original_index(visible_row)
        if original is None:
            return
        if visible_row not in {self.list.row(item) for item in self.list.selectedItems()}:
            self.list.clearSelection()
            self.list.setCurrentRow(visible_row)
        item = self._items[original]
        menu = QMenu(self)
        fav_text = "Unfavorite" if item.favorite else "Favorite"
        favorite_action = menu.addAction(fav_text)
        favorite_action.triggered.connect(lambda: self.toggle_favorite.emit(original, not item.favorite))
        menu.addSeparator()
        properties_action = menu.addAction("Properties")
        properties_action.triggered.connect(self._emit_properties_selected)
        menu.addSeparator()
        delete_action = menu.addAction("Remove")
        delete_action.triggered.connect(self._emit_remove_selected)
        menu.exec(self.list.viewport().mapToGlobal(pos))

    def _emit_properties_selected(self) -> None:
        original = self._current_original_index()
        if original is None:
            return
        self.list.clearSelection()
        visible = self._visible_row(original)
        if visible is not None:
            self.list.setCurrentRow(visible)
        self.frame_preview.show_properties()

    def _emit_remove_selected(self) -> None:
        rows = self._selected_original_indices()
        if rows:
            self.remove_clicked.emit(rows)

    def _on_rows_moved(self, *_args: object) -> None:
        if self._updating:
            return
        self._emit_reorder_from_list()

    def _emit_reorder_from_list(self) -> None:
        """Rebuild ImageItem tuple from current list widget order.

        Reordering is disabled while a filter is active because hidden frames
        have no visible drop position.
        """
        if len(self._display_indices) != len(self._items):
            return
        ordered: list[ImageItem] = []
        for visible in range(self.list.count()):
            row = self.list.item(visible)
            path = row.data(Qt.ItemDataRole.UserRole)
            if not isinstance(path, Path):
                path = Path(str(path))
            original = self._display_indices[visible]
            base = self._items[original]
            if base.path != path:
                base = next((it for it in self._items if it.path == path), None)
            if base is None:
                continue
            enabled = row.checkState() == Qt.CheckState.Checked
            ordered.append(
                ImageItem(
                    path=base.path,
                    enabled=enabled,
                    detection_ok=base.detection_ok,
                    thumbnail_path=base.thumbnail_path,
                    favorite=base.favorite,
                )
            )
        if ordered and tuple(ordered) != self._items:
            self._items = tuple(ordered)
            self.reorder_images.emit(self._items)

    def _row_label(self, item: ImageItem) -> str:
        """Filename with favorite and disc-detection markers."""
        star = _STAR_ON if item.favorite else _STAR_OFF
        label = item.path.name
        if item.detection_ok is True:
            return f"{star} {label}"
        if item.detection_ok is False:
            return f"{star} ✗ {label}"
        return f"{star} {label}"

    def _simple_row_label(self, item: ImageItem) -> str:
        star = _STAR_ON if item.favorite else _STAR_OFF
        if item.detection_ok is True:
            return f"{star} {item.path.name}"
        if item.detection_ok is False:
            return f"{star} ✗ {item.path.name}"
        return f"{star} {item.path.name}"

    def _icon_label(self, item: ImageItem) -> str:
        return f"{_STAR_ON if item.favorite else _STAR_OFF}\n{item.path.name}"

    def _icon_for(self, item: ImageItem) -> QIcon:
        """Return a cached list icon for *item*, or empty if none."""
        path = item.thumbnail_path
        if not path:
            return QIcon()
        cached = self._icons.get(path)
        if cached is not None:
            return cached
        pix = _pixmap_from_thumb(path)
        icon = QIcon() if pix.isNull() else QIcon(pix)
        self._icons[path] = icon
        return icon

    def _apply_row_style(self, row: QListWidgetItem, item: ImageItem, *, simple: bool = False) -> None:
        """Sync label, icon, and detection colour for one list row."""
        if simple:
            row.setText(self._simple_row_label(item))
            row.setIcon(QIcon())
        else:
            row.setText(self._row_label(item))
            row.setIcon(self._icon_for(item))
        if item.detection_ok is False:
            row.setForeground(QColor(COLOR.danger))
        else:
            row.setData(Qt.ItemDataRole.ForegroundRole, None)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            rows = self._selected_original_indices()
            if not rows:
                row = self._current_original_index()
                if row is not None:
                    rows = (row,)
            if rows:
                self.remove_clicked.emit(rows)
                event.accept()
                return
        if event.key() == Qt.Key.Key_F:
            original = self._current_original_index()
            if original is not None:
                item = self._items[original]
                self.toggle_favorite.emit(original, not item.favorite)
                event.accept()
                return
        super().keyPressEvent(event)

    def _on_view_mode_changed(self, index: int) -> None:
        mode = GalleryViewMode.LIST_PREVIEW
        if index == 1:
            mode = GalleryViewMode.LIST_SIMPLE
        elif index == 2:
            mode = GalleryViewMode.ICON
        self.view_mode_changed.emit(mode)

    def _configure_list_for_mode(self, mode: GalleryViewMode) -> None:
        if mode == GalleryViewMode.ICON:
            self.list.setViewMode(QListWidget.ViewMode.IconMode)
            self.list.setFlow(QListWidget.Flow.LeftToRight)
            self.list.setWrapping(True)
            self.list.setGridSize(QSize(_ICON_THUMB_SIZE + 16, _ICON_THUMB_SIZE + 44))
            self.list.setIconSize(QSize(_ICON_THUMB_SIZE, _ICON_THUMB_SIZE))
            self.list.setSpacing(6)
            self.list.setStyleSheet(_ICON_QSS)
            self.list.setDragEnabled(len(self._display_indices) == len(self._items))
        elif mode == GalleryViewMode.LIST_SIMPLE:
            self.list.setViewMode(QListWidget.ViewMode.ListMode)
            self.list.setFlow(QListWidget.Flow.TopToBottom)
            self.list.setWrapping(False)
            self.list.setGridSize(QSize())
            self.list.setIconSize(QSize(_THUMB_SIZE, _THUMB_SIZE))
            self.list.setSpacing(1)
            self.list.setStyleSheet(_LIST_SIMPLE_QSS)
            self.list.setDragEnabled(len(self._display_indices) == len(self._items))
        else:
            self.list.setViewMode(QListWidget.ViewMode.ListMode)
            self.list.setFlow(QListWidget.Flow.TopToBottom)
            self.list.setWrapping(False)
            self.list.setGridSize(QSize())
            self.list.setIconSize(QSize(_THUMB_SIZE, _THUMB_SIZE))
            self.list.setSpacing(2)
            self.list.setStyleSheet(_LIST_PREVIEW_QSS)
            self.list.setDragEnabled(len(self._display_indices) == len(self._items))

    def _build_display_indices(self, state: ScreenState) -> list[int]:
        if not state.gallery_show_only_favorites:
            return list(range(len(state.images)))
        selected = state.selected_index
        return [
            idx
            for idx, item in enumerate(state.images)
            if item.favorite or idx == selected
        ]

    def _sync_toolbar(self, state: ScreenState) -> None:
        self._updating = True
        try:
            if state.gallery_view_mode == GalleryViewMode.LIST_SIMPLE:
                self.view_mode.setCurrentIndex(1)
            elif state.gallery_view_mode == GalleryViewMode.ICON:
                self.view_mode.setCurrentIndex(2)
            else:
                self.view_mode.setCurrentIndex(0)
            self.sort_mode.setCurrentData(state.gallery_sort_mode)
            self.favorites_filter.setChecked(state.gallery_show_only_favorites)
        finally:
            self._updating = False

        busy = (
            state.import_status == JobStatus.RUNNING
            or state.export_status == JobStatus.RUNNING
            or state.preview_status == JobStatus.RUNNING
        )
        self.import_btn.setEnabled(not busy)

    def _sync_import_enabled(self, state: ScreenState) -> None:
        busy = (
            state.import_status == JobStatus.RUNNING
            or state.export_status == JobStatus.RUNNING
            or state.preview_status == JobStatus.RUNNING
        )
        self.import_btn.setEnabled(not busy)

    def _update_count(self, items: tuple[ImageItem, ...]) -> None:
        """Refresh the enabled/total caption in the gallery header."""
        if not items:
            self._count.setText("")
            return
        enabled = sum(1 for item in items if item.enabled)
        favorites = sum(1 for item in items if item.favorite)
        suffix = f" · {favorites} ★" if favorites else ""
        self._count.setText(f"{enabled} of {len(items)}{suffix}")

    def render(self, state: ScreenState) -> None:
        """Rebuild the list to match *state.images*."""
        self._sync_toolbar(state)
        new_items = state.images
        if not new_items:
            self._icons.clear()

        self._items = new_items
        display = self._build_display_indices(state)
        self._display_indices = display
        self._configure_list_for_mode(state.gallery_view_mode)
        drag_enabled = len(display) == len(new_items)
        self.list.setDragEnabled(drag_enabled)
        self._hint.setText("Drag to reorder" if drag_enabled else "Disable favorites filter to reorder")

        self._updating = True
        try:
            current_original = state.selected_index
            current_visible: int | None = None
            if current_original is not None:
                try:
                    current_visible = display.index(current_original)
                except ValueError:
                    current_visible = None

            self.list.clear()
            for visible, original in enumerate(display):
                item = new_items[original]
                row = QListWidgetItem()
                row.setData(Qt.ItemDataRole.UserRole, item.path)
                row.setFlags(
                    row.flags()
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsDragEnabled
                    | Qt.ItemFlag.ItemIsDropEnabled
                )
                row.setCheckState(
                    Qt.CheckState.Checked if item.enabled else Qt.CheckState.Unchecked
                )
                if state.gallery_view_mode == GalleryViewMode.ICON:
                    row.setText(self._icon_label(item))
                    row.setIcon(self._icon_for(item))
                    row.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif state.gallery_view_mode == GalleryViewMode.LIST_SIMPLE:
                    self._apply_row_style(row, item, simple=True)
                    row.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    self._apply_row_style(row, item, simple=False)
                    row.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.list.addItem(row)

            if current_visible is not None:
                self.list.setCurrentRow(current_visible)
        finally:
            self._updating = False

        self._sync_favorite_button()
        self.frame_preview.render(state)
        self._update_count(new_items)
        self._sync_import_enabled(state)
