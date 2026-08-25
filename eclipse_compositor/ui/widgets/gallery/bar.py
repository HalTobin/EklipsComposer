"""Gallery panel composing header, toolbar, frame list, empty state, and frame preview."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QSplitter,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.state import GallerySortMode, GalleryViewMode, ImageItem, JobStatus, ScreenState
from eclipse_compositor.ui.theme import COLOR, EmptyState, HintLabel
from eclipse_compositor.ui.widgets.gallery.header import GalleryHeader
from eclipse_compositor.ui.widgets.gallery.index_map import DisplayIndexMap
from eclipse_compositor.ui.widgets.gallery.list import FrameListWidget
from eclipse_compositor.ui.widgets.gallery.preview import FramePreview
from eclipse_compositor.ui.widgets.gallery.toolbar import GalleryToolbar


class GalleryBar(QWidget):
    """Right-hand sidebar with project media explorer and canvas media list."""

    toggle_image = Signal(int, bool)
    toggle_favorite = Signal(int, bool)
    select_image = Signal(object)  # int | None
    adjust_circle_requested = Signal(int)
    remove_clicked = Signal(object)  # tuple[int, ...] | int | None
    reorder_images = Signal(object)  # tuple[ImageItem, ...]
    files_dropped = Signal(object)  # tuple[Path, ...]
    import_clicked = Signal()
    view_mode_changed = Signal(object)  # GalleryViewMode
    sort_mode_changed = Signal(object)  # GallerySortMode
    show_only_favorites_changed = Signal(bool)
    canvas_view_mode_changed = Signal(object)  # GalleryViewMode
    select_all_clicked = Signal()
    unselect_all_clicked = Signal()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("gallery")
        self._items: tuple[ImageItem, ...] = ()
        self._index_map = DisplayIndexMap()
        self._canvas_items: tuple[ImageItem, ...] = ()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.header = GalleryHeader()
        self.toolbar = GalleryToolbar()
        self._hint = HintLabel("Project media and canvas order")
        self._hint.setStyleSheet(f"color: {COLOR.text_faint}; font-size: 11px;")

        self.list_container = QWidget()
        self._stack = QStackedLayout(self.list_container)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self.list = FrameListWidget()
        self.empty_state = EmptyState(
            "No frames yet",
            "Drag photos or videos here, or click Import above",
        )
        self._stack.addWidget(self.list)
        self._stack.addWidget(self.empty_state)

        self.frame_preview = FramePreview()
        self.canvas_toolbar = GalleryToolbar(include_icon_mode=False)
        self.canvas_toolbar.sort_mode.hide()
        self.canvas_toolbar.favorites_btn.hide()
        self.canvas_list = FrameListWidget()
        self.canvas_list.set_canvas_mode(True)

        project_widget = QWidget()
        project_layout = QVBoxLayout(project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.setSpacing(8)
        project_layout.addWidget(self.header)
        project_layout.addWidget(self.toolbar)
        project_layout.addWidget(self._hint)
        project_layout.addWidget(self.list_container)

        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 12, 0, 0)
        canvas_layout.setSpacing(6)
        canvas_title = QLabel("CANVAS MEDIA")
        canvas_title.setStyleSheet(f"color: {COLOR.text_muted}; font-size: 11px; font-weight: 600;")
        canvas_layout.addWidget(canvas_title)
        canvas_layout.addWidget(self.canvas_toolbar)
        canvas_layout.addWidget(self.canvas_list)

        media_split = QSplitter(Qt.Orientation.Vertical)
        media_split.addWidget(project_widget)
        media_split.addWidget(canvas_widget)
        media_split.setHandleWidth(0)
        media_split.setStyleSheet("QSplitter::handle { background: transparent; }")
        media_split.setStretchFactor(0, 1)
        media_split.setStretchFactor(1, 1)
        media_split.setSizes([400, 300])

        layout.addWidget(media_split, stretch=3)
        layout.addWidget(self.frame_preview, stretch=1)
        self.setMinimumWidth(220)

        self.header.import_clicked.connect(self.import_clicked.emit)
        self.header.select_all_clicked.connect(self.select_all_clicked.emit)
        self.header.unselect_all_clicked.connect(self.unselect_all_clicked.emit)
        self.header.toggle_favorite_clicked.connect(self._on_favorite_selected)
        self.header.remove_selected_clicked.connect(self._on_remove_selected)

        self.toolbar.view_mode_changed.connect(self.view_mode_changed.emit)
        self.toolbar.sort_mode_changed.connect(self.sort_mode_changed.emit)
        self.toolbar.show_only_favorites_changed.connect(self.show_only_favorites_changed.emit)
        self.canvas_toolbar.view_mode_changed.connect(self.canvas_view_mode_changed.emit)

        self.empty_state.import_clicked.connect(self.import_clicked.emit)
        self.empty_state.files_dropped.connect(self.files_dropped.emit)

        self.list.files_dropped.connect(self.files_dropped.emit)
        self.list.item_toggled.connect(self.toggle_image.emit)
        self.list.row_selected.connect(self.select_image.emit)
        self.list.rows_reordered.connect(self._on_rows_reordered)
        self.list.remove_requested.connect(self.remove_clicked.emit)
        self.list.toggle_favorite_requested.connect(self.toggle_favorite.emit)
        self.list.show_properties_requested.connect(self.frame_preview.show_properties)
        self.list.adjust_circle_requested.connect(self.adjust_circle_requested.emit)
        self.list.selection_state_changed.connect(self._on_selection_state_changed)
        self.canvas_list.row_selected.connect(self._on_canvas_row_selected)
        self.canvas_list.rows_reordered.connect(self._on_canvas_rows_reordered)
        self.canvas_list.remove_requested.connect(self._on_remove_canvas_frames)

    def _on_selection_state_changed(self, has_selection: bool, has_current: bool) -> None:
        has_items = bool(self._items)
        self.header.set_selection_actions_enabled(has_selection or has_current, has_items)

    def _on_remove_selected(self) -> None:
        rows = self.list.selected_original_indices()
        if not rows:
            current = self.list.current_original_index()
            if current is not None:
                rows = (current,)
        if rows:
            self.remove_clicked.emit(rows)

    def _on_favorite_selected(self) -> None:
        current = self.list.current_original_index()
        if current is None or current >= len(self._items):
            return
        item = self._items[current]
        self.toggle_favorite.emit(current, not item.favorite)

    def _on_rows_reordered(self, rows_data: tuple[tuple[Path, bool], ...]) -> None:
        reordered = self._index_map.reorder_items(rows_data)
        if reordered is not None:
            self._items = reordered
            self.reorder_images.emit(reordered)

    def _on_canvas_row_selected(self, canvas_index: int | None) -> None:
        if canvas_index is None or not (0 <= canvas_index < len(self._canvas_items)):
            return
        path = self._canvas_items[canvas_index].path
        for image_index, item in enumerate(self._items):
            if item.path == path:
                self.select_image.emit(image_index)
                return

    def _on_canvas_rows_reordered(
        self, rows_data: tuple[tuple[Path, bool], ...]
    ) -> None:
        ordered_paths = [path for path, _enabled in rows_data]
        if len(ordered_paths) != len(self._canvas_items):
            return
        items_by_path = {item.path: item for item in self._canvas_items}
        if set(ordered_paths) != set(items_by_path):
            return

        ordered_canvas_items = iter(items_by_path[path] for path in ordered_paths)
        reordered_images = tuple(
            next(ordered_canvas_items) if item.enabled else item
            for item in self._items
        )
        if reordered_images != self._items:
            self._items = reordered_images
            self.reorder_images.emit(reordered_images)

    def _on_remove_canvas_frames(self, canvas_indices: tuple[int, ...]) -> None:
        canvas_paths = {
            self._canvas_items[index].path
            for index in canvas_indices
            if 0 <= index < len(self._canvas_items)
        }
        for image_index, item in enumerate(self._items):
            if item.path in canvas_paths:
                self.toggle_image.emit(image_index, False)

    def render(self, state: ScreenState) -> None:
        """Rebuild and synchronize the gallery with application state."""
        self._items = state.images
        index_map = DisplayIndexMap(
            images=state.images,
            show_only_favorites=state.gallery_show_only_favorites,
            selected_index=state.selected_index,
        )
        self._index_map = index_map

        enabled_count = sum(1 for it in state.images if it.enabled)
        fav_count = sum(1 for it in state.images if it.favorite)
        self.header.set_counts(enabled_count, len(state.images), fav_count)

        busy = (
            state.import_status == JobStatus.RUNNING
            or state.export_status == JobStatus.RUNNING
            or state.preview_status == JobStatus.RUNNING
        )
        self.header.set_import_enabled(not busy)
        self.empty_state.set_import_enabled(not busy)

        self.toolbar.sync(
            state.gallery_view_mode,
            state.gallery_sort_mode,
            state.gallery_show_only_favorites,
        )

        if not state.images:
            self._stack.setCurrentWidget(self.empty_state)
            self._hint.setText("Import photos or video to assemble your eclipse")
        else:
            self._stack.setCurrentWidget(self.list)
            drag_enabled = index_map.can_reorder
            self._hint.setText(
                "Drag frames to reorder composition" if drag_enabled else "Disable favorites filter to reorder"
            )

        self.list.populate(
            state.images,
            index_map,
            state.gallery_view_mode,
            state.selected_index,
        )
        self.frame_preview.render(state)
        self._canvas_items = tuple(item for item in state.images if item.enabled)
        selected_canvas_index = next(
            (
                index
                for index, item in enumerate(self._canvas_items)
                if state.selected_index is not None
                and item.path == state.images[state.selected_index].path
            ),
            None,
        )
        canvas_index_map = DisplayIndexMap(
            images=self._canvas_items,
            selected_index=selected_canvas_index,
        )
        self.canvas_toolbar.sync(
            state.canvas_gallery_view_mode,
            GallerySortMode.TITLE,
            False,
        )
        self.canvas_list.populate(
            self._canvas_items,
            canvas_index_map,
            state.canvas_gallery_view_mode,
            selected_canvas_index,
        )
