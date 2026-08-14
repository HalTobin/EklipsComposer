"""Main screen View — wires widgets to ViewModel.dispatch / render(state)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QWidget,
)

from eclipse_compositor.ui.actions import (
    ClearImages,
    ExportComposite,
    LoadImages,
    OpenProject,
    ReorderImages,
    RequestPreview,
    ResetColorimetry,
    SaveProject,
    SelectImage,
    SelectSidebarTab,
    ToggleImage,
    UpdateArcAngle,
    UpdateBrightness,
    UpdateContrast,
    UpdateCropSize,
    UpdateDirection,
    UpdateGamma,
    UpdateGridColumns,
    UpdateGridRows,
    UpdateLayout,
    UpdateMaskEnabled,
    UpdateMaskFeather,
    UpdateMaskSize,
    UpdateSaturation,
    UpdateSpacing,
    UpdateTemperature,
    UpdateThreshold,
    UpdateZoom,
)
from eclipse_compositor.cv.loading import image_dialog_globs
from eclipse_compositor.cv.video import (
    VideoProbe,
    is_supported_video,
    probe_video,
    video_dialog_globs,
)
from eclipse_compositor.project import PROJECT_SUFFIX, is_project_file
from eclipse_compositor.resources import app_icon_path
from eclipse_compositor.ui.drop_import import mime_has_importable_paths, paths_from_mime
from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.viewmodel import ScreenViewModel
from eclipse_compositor.ui.widgets.gallery import GalleryBar
from eclipse_compositor.ui.widgets.sidebar import Sidebar
from eclipse_compositor.ui.widgets.viewport import PreviewViewport
from eclipse_compositor.ui.widgets.video_import_dialog import confirm_video_import


class ScreenView(QMainWindow):
    """Root window: sidebar | viewport | gallery. Pure render from state."""

    def __init__(self, view_model: ScreenViewModel) -> None:
        super().__init__()
        self.view_model = view_model
        self.setWindowTitle("VulturEklips")
        icon_file = app_icon_path()
        if icon_file.is_file():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1280, 800)

        self.sidebar = Sidebar()
        self.viewport = PreviewViewport()
        self.gallery = GalleryBar()

        root = QWidget()
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        hsplit = QSplitter(Qt.Orientation.Horizontal)
        hsplit.addWidget(self.sidebar)
        hsplit.addWidget(self.viewport)
        hsplit.addWidget(self.gallery)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 4)
        hsplit.setStretchFactor(2, 1)
        hsplit.setSizes([300, 700, 280])
        h.addWidget(hsplit)
        self.setCentralWidget(root)
        self.setAcceptDrops(True)
        self._build_file_menu()

        # Intents → dispatch
        self.sidebar.import_clicked.connect(self._on_import)
        self.sidebar.open_clicked.connect(self._on_open)
        self.sidebar.save_clicked.connect(self._on_save)
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
        self.sidebar.direction_changed.connect(
            lambda v: self.view_model.dispatch(UpdateDirection(v))
        )
        self.sidebar.arc_angle_changed.connect(
            lambda v: self.view_model.dispatch(UpdateArcAngle(v))
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
        self.sidebar.sidebar_tab_changed.connect(
            lambda v: self.view_model.dispatch(SelectSidebarTab(v))
        )
        self.sidebar.contrast_changed.connect(
            lambda v: self.view_model.dispatch(UpdateContrast(v))
        )
        self.sidebar.saturation_changed.connect(
            lambda v: self.view_model.dispatch(UpdateSaturation(v))
        )
        self.sidebar.brightness_changed.connect(
            lambda v: self.view_model.dispatch(UpdateBrightness(v))
        )
        self.sidebar.gamma_changed.connect(
            lambda v: self.view_model.dispatch(UpdateGamma(v))
        )
        self.sidebar.temperature_changed.connect(
            lambda v: self.view_model.dispatch(UpdateTemperature(v))
        )
        self.sidebar.reset_colorimetry_clicked.connect(
            lambda: self.view_model.dispatch(ResetColorimetry())
        )
        self.sidebar.mask_enabled_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMaskEnabled(v))
        )
        self.sidebar.mask_size_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMaskSize(v))
        )
        self.sidebar.mask_feather_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMaskFeather(v))
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
        self.gallery.files_dropped.connect(self._import_paths)
        self.viewport.files_dropped.connect(self._import_paths)
        self.viewport.zoom_changed.connect(
            lambda z: self.view_model.dispatch(UpdateZoom(z))
        )

        self.view_model.state_changed.connect(self.render)
        self._last_preview_ref: object | None = None
        self.render(self.view_model.state)

    def render(self, state: ScreenState) -> None:
        """Single render entry: sync all child widgets to *state*."""
        if state.last_project_path is not None:
            self.setWindowTitle(f"VulturEklips — {state.last_project_path.name}")
        else:
            self.setWindowTitle("VulturEklips")
        self.sidebar.render(state)
        self.gallery.render(state)
        preview = state.preview_bgr
        if preview is not self._last_preview_ref:
            self._last_preview_ref = preview
            # New composite → fit entire image in the viewport by default.
            self.viewport.set_preview(preview, fit=True)  # type: ignore[arg-type]
        elif not self.viewport.is_fit_mode():
            self.viewport.set_zoom(state.zoom)
        has_images = len(state.images) > 0
        busy = (
            state.import_status == JobStatus.RUNNING
            or state.export_status == JobStatus.RUNNING
            or state.preview_status == JobStatus.RUNNING
        )
        self._open_action.setEnabled(not busy)
        self._save_action.setEnabled(not busy and has_images)

    def _import_busy(self) -> bool:
        """True when a drop/import would conflict with a running job."""
        state = self.view_model.state
        return (
            state.import_status == JobStatus.RUNNING
            or state.export_status == JobStatus.RUNNING
        )

    def _accept_import_drag(self, event: QDragEnterEvent | QDragMoveEvent) -> None:
        if self._import_busy() or not mime_has_importable_paths(event.mimeData()):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        self._accept_import_drag(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        self._accept_import_drag(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if self._import_busy():
            event.ignore()
            return
        paths = paths_from_mime(event.mimeData())
        if not paths:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        self._import_paths(tuple(paths))

    def _import_paths(self, paths: tuple[Path, ...]) -> None:
        """Dispatch LoadImages after a file dialog or a drop."""
        if not paths or self._import_busy():
            return
        project_files = [path for path in paths if is_project_file(path)]
        if project_files:
            self._open_project_path(project_files[0])
            return
        videos = [path for path in paths if is_supported_video(path)]
        if videos:
            probes, failed = self._probe_videos(videos)
            if failed:
                details = "\n".join(
                    f"{path.name}: {message}" for path, message in failed
                )
                QMessageBox.warning(
                    self,
                    "Could not read video",
                    "Some videos could not be opened:\n\n" + details,
                )
            video_step = 1
            if probes:
                chosen = confirm_video_import(self, probes)
                if chosen is None:
                    paths = tuple(
                        path for path in paths if not is_supported_video(path)
                    )
                else:
                    video_step = chosen
                    keep_videos = {probe.path for probe in probes}
                    paths = tuple(
                        path
                        for path in paths
                        if not is_supported_video(path) or path in keep_videos
                    )
            else:
                paths = tuple(path for path in paths if not is_supported_video(path))
            if not paths:
                return
            self.view_model.dispatch(LoadImages(paths, video_frame_step=video_step))
            return
        self.view_model.dispatch(LoadImages(paths))

    def _probe_videos(
        self, videos: list[Path]
    ) -> tuple[list[VideoProbe], list[tuple[Path, str]]]:
        """Read frame counts for *videos*. Returns (probes, failures)."""
        probes: list[VideoProbe] = []
        failed: list[tuple[Path, str]] = []
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for video in videos:
                try:
                    probes.append(probe_video(video))
                except Exception as exc:  # noqa: BLE001 — per-file probe fallback
                    failed.append((video, str(exc)))
        finally:
            QApplication.restoreOverrideCursor()
        return probes, failed

    def _on_import(self) -> None:
        image_globs = image_dialog_globs()
        video_globs = video_dialog_globs()
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import eclipse photos or video",
            "",
            "Images and videos "
            f"({image_globs} {video_globs});;"
            f"Images ({image_globs});;"
            f"Videos ({video_globs})",
        )
        if not files:
            return
        self._import_paths(tuple(Path(f) for f in files))

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

    def _build_file_menu(self) -> None:
        """File menu for opening and saving ``.vlt`` projects."""
        menu = self.menuBar().addMenu("&File")
        self._open_action = QAction("Open Project…", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self._on_open)
        menu.addAction(self._open_action)
        self._save_action = QAction("Save Project…", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.triggered.connect(self._on_save)
        menu.addAction(self._save_action)

    def _on_open(self) -> None:
        if self._import_busy():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open project",
            "",
            f"VulturEklips project (*{PROJECT_SUFFIX})",
        )
        if not path:
            return
        self._open_project_path(Path(path))

    def _on_save(self) -> None:
        if self._import_busy():
            return
        if not self.view_model.state.images:
            return
        suggested = "composition.vlt"
        if self.view_model.state.last_project_path is not None:
            suggested = str(self.view_model.state.last_project_path)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save project",
            suggested,
            f"VulturEklips project (*{PROJECT_SUFFIX})",
        )
        if not path:
            return
        out = Path(path)
        if out.suffix.lower() != PROJECT_SUFFIX:
            out = out.with_suffix(PROJECT_SUFFIX)
        self.view_model.dispatch(SaveProject(out))

    def open_project_from_os(self, path: Path | str) -> None:
        """Open a ``.vlt`` launched from Finder, argv, or a file-open event."""
        self._open_project_path(Path(path))

    def _open_project_path(self, path: Path) -> None:
        """Confirm replace if needed, then dispatch OpenProject."""
        if self._import_busy():
            return
        if not path.is_file():
            QMessageBox.warning(
                self,
                "Could not open project",
                f"File not found:\n{path}",
            )
            return
        if self.view_model.state.images:
            answer = QMessageBox.question(
                self,
                "Open project",
                "Opening a project replaces the current composition. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.view_model.dispatch(OpenProject(path))
