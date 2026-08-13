"""Bottom gallery listing imported frames with enable checkboxes."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.state import ImageItem, ScreenState


class GalleryBar(QWidget):
    """Draggable list of imported photos with per-frame enable toggles."""

    toggle_image = Signal(int, bool)
    select_image = Signal(object)  # int | None
    reorder_images = Signal(object)  # tuple[ImageItem, ...]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._updating = False
        self._items: tuple[ImageItem, ...] = ()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        header = QLabel("Frames (drag to reorder)")
        header.setStyleSheet("font-weight: 600;")
        layout.addWidget(header)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list.setDragEnabled(True)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentRowChanged.connect(self._on_row_changed)
        self.list.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self.list)

        hint = QLabel(
            "Drag to set composite order. Uncheck frames to exclude them."
        )
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

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

    def render(self, state: ScreenState) -> None:
        """Rebuild the list to match *state.images*."""
        # Avoid clobbering an in-progress drag with a full rebuild when only
        # detection flags / status changed but order+enable are unchanged.
        new_items = state.images
        if (
            not self._updating
            and self._items
            and len(self._items) == len(new_items)
            and all(
                a.path == b.path and a.enabled == b.enabled
                for a, b in zip(self._items, new_items, strict=True)
            )
        ):
            # Update detection markers in place.
            self._updating = True
            try:
                self._items = new_items
                for i, item in enumerate(new_items):
                    row = self.list.item(i)
                    if row is None:
                        continue
                    label = item.path.name
                    if item.detection_ok is True:
                        label = f"✓ {label}"
                    elif item.detection_ok is False:
                        label = f"✗ {label}"
                    row.setText(label)
                    if item.detection_ok is False:
                        row.setForeground(Qt.GlobalColor.red)
                    else:
                        row.setData(Qt.ItemDataRole.ForegroundRole, None)
            finally:
                self._updating = False
            return

        self._updating = True
        try:
            self._items = new_items
            current = state.selected_index
            self.list.clear()
            for item in new_items:
                label = item.path.name
                if item.detection_ok is True:
                    label = f"✓ {label}"
                elif item.detection_ok is False:
                    label = f"✗ {label}"
                row = QListWidgetItem(label)
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
                if item.detection_ok is False:
                    row.setForeground(Qt.GlobalColor.red)
                self.list.addItem(row)
            if current is not None and 0 <= current < self.list.count():
                self.list.setCurrentRow(current)
        finally:
            self._updating = False
