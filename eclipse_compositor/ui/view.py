"""Main screen View — wires widgets to ViewModel.dispatch / render(state)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from eclipse_compositor.ui.actions import (
    ClearImages,
    ExportComposite,
    LoadImages,
    ReorderImages,
    RequestPreview,
    SelectImage,
    ToggleImage,
    UpdateCropSize,
    UpdateCurvature,
    UpdateGridColumns,
    UpdateGridRows,
    UpdateLayout,
    UpdateSpacing,
    UpdateThreshold,
    UpdateZoom,
)
from eclipse_compositor.resources import app_icon_path
from eclipse_compositor.ui.state import ScreenState
from eclipse_compositor.ui.viewmodel import ScreenViewModel
from eclipse_compositor.ui.widgets.gallery import GalleryBar
from eclipse_compositor.ui.widgets.sidebar import Sidebar
from eclipse_compositor.ui.widgets.viewport import PreviewViewport


class ScreenView(QMainWindow):
    """Root window: sidebar | viewport / gallery. Pure render from state."""

    def __init__(self, view_model: ScreenViewModel) -> None:
        super().__init__()
        self.view_model = view_model
        self.setWindowTitle("VulturEklips — Eclipse Sequence Compositor")
        icon_file = app_icon_path()
        if icon_file.is_file():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1280, 800)

        self.sidebar = Sidebar()
        self.viewport = PreviewViewport()
        self.gallery = GalleryBar()

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.addWidget(self.viewport)
        vsplit.addWidget(self.gallery)
        vsplit.setStretchFactor(0, 4)
        vsplit.setStretchFactor(1, 1)
        center_layout.addWidget(vsplit)

        root = QWidget()
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        hsplit = QSplitter(Qt.Orientation.Horizontal)
        hsplit.addWidget(self.sidebar)
        hsplit.addWidget(center)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 1)
        hsplit.setSizes([280, 1000])
        h.addWidget(hsplit)
        self.setCentralWidget(root)

        # Intents → dispatch
        self.sidebar.import_clicked.connect(self._on_import)
        self.sidebar.clear_clicked.connect(
            lambda: self.view_model.dispatch(ClearImages())
        )
        self.sidebar.preview_clicked.connect(
            lambda: self.view_model.dispatch(RequestPreview())
        )
        self.sidebar.export_clicked.connect(self._on_export)
        self.sidebar.crop_size_changed.connect(
            lambda v: self.view_model.dispatch(UpdateCropSize(v))
        )
        self.sidebar.spacing_changed.connect(
            lambda v: self.view_model.dispatch(UpdateSpacing(v))
        )
        self.sidebar.layout_changed.connect(
            lambda v: self.view_model.dispatch(UpdateLayout(v))
        )
        self.sidebar.curvature_changed.connect(
            lambda v: self.view_model.dispatch(UpdateCurvature(v))
        )
        self.sidebar.threshold_changed.connect(
            lambda v: self.view_model.dispatch(UpdateThreshold(v))
        )
        self.sidebar.grid_columns_changed.connect(
            lambda v: self.view_model.dispatch(UpdateGridColumns(v))
        )
        self.sidebar.grid_rows_changed.connect(
            lambda v: self.view_model.dispatch(UpdateGridRows(v))
        )
        self.gallery.toggle_image.connect(
            lambda i, e: self.view_model.dispatch(ToggleImage(i, e))
        )
        self.gallery.select_image.connect(
            lambda i: self.view_model.dispatch(SelectImage(i))
        )
        self.gallery.reorder_images.connect(
            lambda images: self.view_model.dispatch(ReorderImages(tuple(images)))
        )
        self.viewport.zoom_changed.connect(
            lambda z: self.view_model.dispatch(UpdateZoom(z))
        )

        self.view_model.state_changed.connect(self.render)
        self._last_preview_ref: object | None = None
        self.render(self.view_model.state)

    def render(self, state: ScreenState) -> None:
        """Single render entry: sync all child widgets to *state*."""
        self.sidebar.render(state)
        self.gallery.render(state)
        preview = state.preview_bgr
        if preview is not self._last_preview_ref:
            self._last_preview_ref = preview
            # New composite → fit entire image in the viewport by default.
            self.viewport.set_preview(preview, fit=True)  # type: ignore[arg-type]
        elif not self.viewport.is_fit_mode():
            self.viewport.set_zoom(state.zoom)

    def _on_import(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import eclipse photos",
            "",
            "Images (*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.webp)",
        )
        if not files:
            return
        paths = tuple(Path(f) for f in files)
        self.view_model.dispatch(LoadImages(paths))

    def _on_export(self) -> None:
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export composite",
            "eclipse_composite.tif",
            "TIFF (*.tif *.tiff);;JPEG (*.jpg *.jpeg);;PNG (*.png)",
        )
        if not path:
            return
        out = Path(path)
        if out.suffix == "":
            if "JPEG" in selected_filter:
                out = out.with_suffix(".jpg")
            elif "PNG" in selected_filter:
                out = out.with_suffix(".png")
            else:
                out = out.with_suffix(".tif")
        self.view_model.dispatch(ExportComposite(out))
