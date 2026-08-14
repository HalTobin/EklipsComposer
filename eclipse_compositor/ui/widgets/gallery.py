"""Frame list with enable checkboxes and a compact selected-frame preview."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.cv.loading import load_image_bgr
from eclipse_compositor.ui.drop_import import mime_has_importable_paths, paths_from_mime
from eclipse_compositor.ui.state import ImageItem, ScreenState
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
    reorder_images = Signal(object)  # tuple[ImageItem, ...]
    files_dropped = Signal(object)  # tuple[Path, ...]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._updating = False
        self._items: tuple[ImageItem, ...] = ()
        self._icons: dict[str, QIcon] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)

        header = QLabel("Frames (drag to reorder)")
        header.setStyleSheet("font-weight: 600;")
        self.list = FrameListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list.setDragEnabled(True)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentRowChanged.connect(self._on_row_changed)
        self.list.model().rowsMoved.connect(self._on_rows_moved)
        self.list.files_dropped.connect(self.files_dropped.emit)
        self.list.setMinimumWidth(180)
        self.list.setIconSize(QSize(_THUMB_SIZE, _THUMB_SIZE))
        self.list.setSpacing(2)

        list_pane = QWidget()
        list_layout = QVBoxLayout(list_pane)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(header)
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

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._updating:
            return
        index = self.list.row(item)
        enabled = item.checkState() == Qt.CheckState.Checked
        self.toggle_image.emit(index, enabled)

    def _on_row_changed(self, row: int) -> None:
        if self._updating:
            return
        self.select_image.emit(row if row >= 0 else None)

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
            row.setForeground(Qt.GlobalColor.red)
        else:
            row.setData(Qt.ItemDataRole.ForegroundRole, None)

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
                        row.setForeground(Qt.GlobalColor.red)
                    else:
                        row.setData(Qt.ItemDataRole.ForegroundRole, None)
            finally:
                self._updating = False
            self.frame_preview.render(state)
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
