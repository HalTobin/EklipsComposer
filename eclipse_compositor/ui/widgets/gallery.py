"""Frame list with enable checkboxes and a compact selected-frame preview."""

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
from eclipse_compositor.ui.state import ImageItem, JobStatus, ScreenState
from eclipse_compositor.ui.theme import COLOR, ActionButton, CaptionLabel, HintLabel
from eclipse_compositor.ui.widgets.frame_preview import FramePreview
from eclipse_compositor.ui.widgets.viewport import bgr_to_qimage

_THUMB_SIZE = 48


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
    select_image = Signal(object)  # int | None
    remove_clicked = Signal(object)  # int | None
    reorder_images = Signal(object)  # tuple[ImageItem, ...]
    files_dropped = Signal(object)  # tuple[Path, ...]
    import_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("gallery")
        self._updating = False
        self._items: tuple[ImageItem, ...] = ()
        self._icons: dict[str, QIcon] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        title = CaptionLabel("Frames")
        title.setObjectName("sectionTitle")
        self._count = CaptionLabel()
        self._count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(title)
        header_row.addWidget(self._count, stretch=1)
        hint = HintLabel("Drag to reorder")
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

        list_pane = QWidget()
        list_layout = QVBoxLayout(list_pane)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)
        row_buttons = QHBoxLayout()
        self.import_btn = ActionButton("Import")
        self.remove_btn = ActionButton("Remove", variant="ghost")
        self.remove_btn.setEnabled(False)
        row_buttons.addWidget(self.import_btn)
        row_buttons.addWidget(self.remove_btn)
        list_layout.addLayout(row_buttons)
        list_layout.addLayout(header_row)
        list_layout.addWidget(hint)
        list_layout.addWidget(self.list)

        self.frame_preview = FramePreview()

        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(list_pane)
        split.addWidget(self.frame_preview)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        split.setSizes([520, 140])
        layout.addWidget(split)
        self.setMinimumWidth(220)

        self.import_btn.clicked.connect(self.import_clicked.emit)
        self.remove_btn.clicked.connect(self._on_remove_selected)

    def _on_remove_selected(self) -> None:
        rows = self._selected_row_indices()
        if not rows:
            row = self.list.currentRow()
            if row >= 0:
                rows = (row,)
            else:
                return
        self.remove_clicked.emit(rows)

    def _selected_row_indices(self) -> tuple[int, ...]:
        return tuple(sorted({self.list.row(item) for item in self.list.selectedItems()}))

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._updating:
            return
        index = self.list.row(item)
        enabled = item.checkState() == Qt.CheckState.Checked
        self.toggle_image.emit(index, enabled)

    def _on_selection_changed(self) -> None:
        self.remove_btn.setEnabled(bool(self.list.selectedItems()))

    def _on_row_changed(self, row: int) -> None:
        if self._updating:
            return
        self.remove_btn.setEnabled(row >= 0 or bool(self.list.selectedItems()))
        self.select_image.emit(row if row >= 0 else None)

    def _on_context_menu(self, pos) -> None:
        row = self.list.row(self.list.itemAt(pos))
        if row < 0:
            return
        if row not in self._selected_row_indices():
            self.list.clearSelection()
            self.list.setCurrentRow(row)
        menu = QMenu(self)
        properties_action = menu.addAction("Properties")
        properties_action.triggered.connect(self._emit_properties_selected)
        menu.addSeparator()
        delete_action = menu.addAction("Remove")
        delete_action.triggered.connect(self._emit_remove_selected)
        menu.exec(self.list.viewport().mapToGlobal(pos))

    def _emit_properties_selected(self) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        self.list.clearSelection()
        self.list.setCurrentRow(row)
        self.frame_preview.show_properties()

    def _emit_remove_selected(self) -> None:
        rows = self._selected_row_indices()
        if rows:
            self.remove_clicked.emit(rows)

    def _on_rows_moved(self, *_args: object) -> None:
        if self._updating:
            return
        self._emit_reorder_from_list()

    def _emit_reorder_from_list(self) -> None:
        """Rebuild ImageItem tuple from current list widget order."""
        by_path = {item.path: item for item in self._items}
        ordered: list[ImageItem] = []
        for i in range(self.list.count()):
            row = self.list.item(i)
            path = row.data(Qt.ItemDataRole.UserRole)
            if not isinstance(path, Path):
                path = Path(str(path))
            base = by_path.get(path)
            if base is None:
                continue
            enabled = row.checkState() == Qt.CheckState.Checked
            ordered.append(
                ImageItem(
                    path=base.path,
                    enabled=enabled,
                    detection_ok=base.detection_ok,
                    thumbnail_path=base.thumbnail_path,
                )
            )
        if ordered and tuple(ordered) != self._items:
            self._items = tuple(ordered)
            self.reorder_images.emit(self._items)

    def _row_label(self, item: ImageItem) -> str:
        """Filename with a disc-detection marker prefix."""
        label = item.path.name
        if item.detection_ok is True:
            return f"✓ {label}"
        if item.detection_ok is False:
            return f"✗ {label}"
        return label

    def _icon_for(self, item: ImageItem) -> QIcon:
        """Return a cached list icon for *item*, or empty if none.

        Thumbnails are JPEG files decoded with Pillow. ``QPixmap(path)`` is
        not used: the macOS bundle strips Qt's ``libqjpeg`` plugin, so Qt
        cannot read those files even when they exist on disk.
        """
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

    def _apply_row_style(self, row: QListWidgetItem, item: ImageItem) -> None:
        """Sync label, icon, and detection colour for one list row."""
        row.setText(self._row_label(item))
        row.setIcon(self._icon_for(item))
        if item.detection_ok is False:
            row.setForeground(QColor(COLOR.danger))
        else:
            row.setData(Qt.ItemDataRole.ForegroundRole, None)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            rows = self._selected_row_indices()
            if not rows:
                row = self.list.currentRow()
                if row >= 0:
                    rows = (row,)
            if rows:
                self.remove_clicked.emit(rows)
                event.accept()
                return
        super().keyPressEvent(event)

    def render(self, state: ScreenState) -> None:
        """Rebuild the list to match *state.images*."""
        # Avoid clobbering an in-progress drag with a full rebuild when only
        # detection flags / status changed but order+enable are unchanged.
        new_items = state.images
        if not new_items:
            self._icons.clear()
        if (
            not self._updating
            and self._items
            and len(self._items) == len(new_items)
            and all(
                a.path == b.path and a.enabled == b.enabled
                for a, b in zip(self._items, new_items, strict=True)
            )
        ):
            # Update detection markers in place (keep thumbnails as-is).
            self._updating = True
            try:
                self._items = new_items
                for i, item in enumerate(new_items):
                    row = self.list.item(i)
                    if row is None:
                        continue
                    row.setText(self._row_label(item))
                    if item.detection_ok is False:
                        row.setForeground(QColor(COLOR.danger))
                    else:
                        row.setData(Qt.ItemDataRole.ForegroundRole, None)
            finally:
                self._updating = False
            self.frame_preview.render(state)
            self._update_count(new_items)
            self._sync_import_enabled(state)
            return

        self._updating = True
        try:
            self._items = new_items
            current = state.selected_index
            self.list.clear()
            for item in new_items:
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
                self._apply_row_style(row, item)
                self.list.addItem(row)
            if current is not None and 0 <= current < self.list.count():
                self.list.setCurrentRow(current)
        finally:
            self._updating = False
        self.frame_preview.render(state)
        self._update_count(new_items)
        self._sync_import_enabled(state)

    def _sync_import_enabled(self, state: ScreenState) -> None:
        """Disable Import while a background job is running."""
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
        self._count.setText(f"{enabled} of {len(items)}")
