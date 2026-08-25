"""Main screen View — wires widgets to ViewModel.dispatch / render(state)."""

from __future__ import annotations

import logging
import sys
from ctypes import c_bool, c_char_p, c_double, c_uint, c_void_p, cdll, util
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QCloseEvent,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeySequence,
    QResizeEvent,
)
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
    ApplyImageDetectionOverride,
    CancelJob,
    ClearImages,
    ExportComposite,
    LoadImages,
    OpenProject,
    RemoveImage,
    ReorderImages,
    RequestPreview,
    ResetColorimetry,
    SaveProject,
    SelectImage,
    SelectSidebarTab,
    SetAllEnabled,
    ToggleFavorite,
    ToggleImage,
    UpdateArcAngle,
    UpdateBrightness,
    UpdateCanvasGalleryViewMode,
    UpdateContrast,
    UpdateCropSize,
    UpdateDirection,
    UpdateGamma,
    UpdateGalleryShowOnlyFavorites,
    UpdateGallerySortMode,
    UpdateGalleryViewMode,
    UpdateProjectGalleryHidden,
    UpdateGridColumns,
    UpdateGridRows,
    UpdateLayout,
    UpdateMaskEnabled,
    UpdateMaskFeather,
    UpdateMaskSize,
    UpdateMarginGlobal,
    UpdateMarginLinked,
    UpdateMarginX,
    UpdateMarginY,
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
from eclipse_compositor.ui.licenses import show_licenses_dialog
from eclipse_compositor.ui.state import JobStatus, ScreenState
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_view import AdjustCircleView
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_viewmodel import AdjustCircleViewModel
from eclipse_compositor.ui.feature.adjust_circle.adjust_circle_actions import OpenAdjustCircle
from eclipse_compositor.ui.theme import qicon_from_path
from eclipse_compositor.ui.viewmodel import ScreenViewModel
from eclipse_compositor.ui.widgets.about_dialog import show_about_dialog
from eclipse_compositor.ui.widgets.gallery import GalleryBar
from eclipse_compositor.ui.widgets.sidebar import Sidebar
from eclipse_compositor.ui.widgets.fullscreen_preview import FullscreenPreview
from eclipse_compositor.ui.widgets.job_overlay import JobOverlay
from eclipse_compositor.ui.widgets.viewport import ViewportPane

if sys.platform == "darwin":
    try:
        from PySide6.QtGui import QWindow
    except ImportError:
        QWindow = None
else:
    QWindow = None
from eclipse_compositor.ui.widgets.video_import_dialog import confirm_video_import


class ScreenView(QMainWindow):
    """Root window: sidebar | viewport | gallery. Pure render from state."""

    def __init__(self, view_model: ScreenViewModel) -> None:
        super().__init__()
        self.view_model = view_model
        self.setWindowTitle("EklipsComposer")
        icon = qicon_from_path(app_icon_path())
        if not icon.isNull():
            self.setWindowIcon(icon)
        self._macos_titlebar_style_applied = False
        self.resize(1440, 880)
        self.sidebar = Sidebar()
        self.viewport = ViewportPane()
        self.gallery = GalleryBar()

        root = QWidget()
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        hsplit = QSplitter(Qt.Orientation.Horizontal)
        hsplit.setHandleWidth(1)
        hsplit.setChildrenCollapsible(False)
        hsplit.addWidget(self.sidebar)
        hsplit.addWidget(self.viewport)
        hsplit.addWidget(self.gallery)
        hsplit.setStretchFactor(0, 0)
        hsplit.setStretchFactor(1, 4)
        hsplit.setStretchFactor(2, 1)
        hsplit.setSizes([360, 760, 300])
        h.addWidget(hsplit)
        self.setCentralWidget(root)
        self.setAcceptDrops(True)
        self._fullscreen: FullscreenPreview | None = None
        self._pending_after_save: str | None = None
        self._pending_open_path: Path | None = None
        self.job_overlay = JobOverlay(root)
        self._build_menus()
        self._wire_intents()

    def _apply_macos_titlebar_style(self) -> None:
        if sys.platform != "darwin":
            return
        if QApplication.platformName() != "cocoa":
            return

        if hasattr(self, "setUnifiedTitleAndToolBarOnMac"):
            try:
                self.setUnifiedTitleAndToolBarOnMac(True)
            except Exception:
                pass

        try:
            self.winId()
            lib_path = util.find_library("objc")
            if lib_path is None:
                return
            objc = cdll.LoadLibrary(lib_path)
            objc.objc_getClass.restype = c_void_p
            objc.objc_getClass.argtypes = [c_char_p]
            objc.sel_registerName.restype = c_void_p
            objc.sel_registerName.argtypes = [c_char_p]

            def _msg(restype, receiver, selector, *args, argtypes=()):
                objc.objc_msgSend.restype = restype
                objc.objc_msgSend.argtypes = [c_void_p, c_void_p, *argtypes]
                return objc.objc_msgSend(receiver, selector, *args)

            ns_view = c_void_p(int(self.winId()))
            if not ns_view.value:
                return
            ns_window = _msg(c_void_p, ns_view, objc.sel_registerName(b"window"))
            if not ns_window:
                return
            ns_color_class = objc.objc_getClass(b"NSColor")
            color = self.palette().color(self.backgroundRole())
            ns_color = _msg(
                c_void_p,
                ns_color_class,
                objc.sel_registerName(b"colorWithDeviceRed:green:blue:alpha:"),
                c_double(color.redF()),
                c_double(color.greenF()),
                c_double(color.blueF()),
                c_double(color.alphaF()),
                argtypes=(c_double, c_double, c_double, c_double),
            )
            _msg(None, ns_window, objc.sel_registerName(b"setBackgroundColor:"), ns_color, argtypes=(c_void_p,))
            _msg(None, ns_window, objc.sel_registerName(b"setTitlebarAppearsTransparent:"), True, argtypes=(c_bool,))
        except Exception as exc:
            logging.getLogger(__name__).debug(
                "Could not apply macOS titlebar background style",
                exc_info=exc,
            )

    def _wire_intents(self) -> None:
        self.gallery.import_clicked.connect(self._on_import)
        self.viewport.import_clicked.connect(self._on_import)
        self.sidebar.fullscreen_clicked.connect(self._on_fullscreen_preview)
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
        self.sidebar.margin_linked_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMarginLinked(v))
        )
        self.sidebar.margin_global_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMarginGlobal(v))
        )
        self.sidebar.margin_x_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMarginX(v))
        )
        self.sidebar.margin_y_changed.connect(
            lambda v: self.view_model.dispatch(UpdateMarginY(v))
        )
        self.gallery.toggle_image.connect(
            lambda i, e: self.view_model.dispatch(ToggleImage(i, e))
        )
        self.gallery.toggle_favorite.connect(
            lambda i, f: self.view_model.dispatch(ToggleFavorite(i, f))
        )
        self.gallery.adjust_circle_requested.connect(self._on_adjust_circle_requested)
        self.gallery.remove_clicked.connect(
            lambda indices: self.view_model.dispatch(
                RemoveImage(tuple(indices) if isinstance(indices, tuple) else (indices,))
            )
        )
        self.gallery.select_image.connect(
            lambda i: self.view_model.dispatch(SelectImage(i))
        )
        self.gallery.reorder_images.connect(
            lambda images: self.view_model.dispatch(ReorderImages(tuple(images)))
        )
        self.gallery.files_dropped.connect(self._import_paths)
        self.gallery.view_mode_changed.connect(
            lambda v: self.view_model.dispatch(UpdateGalleryViewMode(v))
        )
        self.gallery.canvas_view_mode_changed.connect(
            lambda v: self.view_model.dispatch(UpdateCanvasGalleryViewMode(v))
        )
        self.gallery.project_gallery_hidden_changed.connect(
            lambda hidden: self.view_model.dispatch(UpdateProjectGalleryHidden(hidden))
        )
        self.gallery.sort_mode_changed.connect(
            lambda v: self.view_model.dispatch(UpdateGallerySortMode(v))
        )
        self.gallery.show_only_favorites_changed.connect(
            lambda v: self.view_model.dispatch(UpdateGalleryShowOnlyFavorites(v))
        )
        self.gallery.select_all_clicked.connect(
            lambda: self.view_model.dispatch(SetAllEnabled(True))
        )
        self.gallery.unselect_all_clicked.connect(
            lambda: self.view_model.dispatch(SetAllEnabled(False))
        )
        self.viewport.files_dropped.connect(self._import_paths)
        self.viewport.zoom_changed.connect(
            lambda z: self.view_model.dispatch(UpdateZoom(z))
        )
        self.viewport.full_clicked.connect(self._on_fullscreen_preview)
        self.job_overlay.cancel_clicked.connect(
            lambda: self.view_model.dispatch(CancelJob())
        )

        self.view_model.state_changed.connect(self.render)
        self._last_preview_ref: object | None = None
        self._adjust_circle_vm = AdjustCircleViewModel(self)
        self._adjust_circle_vm.manual_detection_applied.connect(
            self._on_manual_detection_applied
        )
        self.render(self.view_model.state)

    def render(self, state: ScreenState) -> None:
        """Single render entry: sync all child widgets to *state*."""
        if state.last_project_path is not None:
            self.setWindowTitle(f"EklipsComposer — {state.last_project_path.name}[*]")
        else:
            self.setWindowTitle("EklipsComposer[*]")
        self.setWindowModified(state.dirty)
        self.sidebar.render(state)
        self.gallery.render(state)
        preview = state.preview_bgr
        if preview is not self._last_preview_ref:
            self._last_preview_ref = preview
            # New composite → fit entire image in the viewport by default.
            self.viewport.set_preview(preview, fit=True)  # type: ignore[arg-type]
            if self._fullscreen is not None and self._fullscreen.isVisible():
                if preview is None:
                    self._fullscreen.close()
                else:
                    self._fullscreen.set_preview(preview, fit=True)  # type: ignore[arg-type]
        elif not self.viewport.is_fit_mode():
            self.viewport.set_zoom(state.zoom)
        has_images = len(state.images) > 0
        has_project = state.last_project_path is not None
        locked = state.blocking_job is not None
        busy = (
            locked
            or state.import_status == JobStatus.RUNNING
            or state.export_status == JobStatus.RUNNING
            or state.preview_status == JobStatus.RUNNING
        )
        self.menuBar().setEnabled(not locked)
        self._new_action.setEnabled(not busy and has_images)
        self._open_action.setEnabled(not busy)
        self._save_action.setEnabled(not busy and has_images and has_project)
        self._save_as_action.setEnabled(not busy and has_images)
        self._export_action.setEnabled(not busy and has_images)
        self._fullscreen_action.setEnabled(state.preview_bgr is not None)
        self.viewport.set_import_enabled(not busy)
        self.job_overlay.render(state)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._macos_titlebar_style_applied:
            self._apply_macos_titlebar_style()
            self._macos_titlebar_style_applied = True
        self._layout_job_overlay()
        self._complete_pending_after_save(self.view_model.state)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._layout_job_overlay()

    def _layout_job_overlay(self) -> None:
        """Keep the lock overlay covering the editor chrome."""
        central = self.centralWidget()
        if central is None:
            return
        self.job_overlay.setGeometry(central.rect())
        if self.view_model.state.blocking_job is not None:
            self.job_overlay.raise_()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.view_model.state.blocking_job is not None:
            event.ignore()
            return
        if not self.view_model.state.dirty:
            event.accept()
            return
        if self._pending_after_save is not None:
            event.ignore()
            return
        if self._offer_save_before("close"):
            event.accept()
            return
        event.ignore()

    def _offer_save_before(
        self, action: str, *, open_path: Path | None = None
    ) -> bool:
        """Ask to save dirty work. True means the caller may proceed now."""
        state = self.view_model.state
        if not state.dirty:
            return True
        name = (
            state.last_project_path.name
            if state.last_project_path is not None
            else "Untitled"
        )
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Unsaved changes")
        box.setText(f'Do you want to save the changes to “{name}”?')
        box.setInformativeText("Your changes will be lost if you don't save them.")
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Save)
        result = box.exec()
        if result == QMessageBox.StandardButton.Discard:
            return True
        if result == QMessageBox.StandardButton.Save:
            self._begin_save_then(action, open_path=open_path)
        return False

    def _begin_save_then(
        self, action: str, *, open_path: Path | None = None
    ) -> None:
        """Save, then run *action* (``new``, ``close``, or ``open``)."""
        state = self.view_model.state
        path = state.last_project_path
        if path is None:
            path = self._choose_save_path()
            if path is None:
                return
        self._pending_after_save = action
        self._pending_open_path = open_path
        if state.export_status != JobStatus.RUNNING:
            self.view_model.dispatch(SaveProject(path))

    def _complete_pending_after_save(self, state: ScreenState) -> None:
        """Finish New / Close / Open once a prompted save has settled."""
        pending = self._pending_after_save
        if pending is None:
            return
        if state.export_status == JobStatus.RUNNING:
            return
        if state.dirty:
            self._pending_after_save = None
            self._pending_open_path = None
            return
        self._pending_after_save = None
        open_path = self._pending_open_path
        self._pending_open_path = None
        if pending == "new":
            QTimer.singleShot(0, lambda: self.view_model.dispatch(ClearImages()))
        elif pending == "close":
            QTimer.singleShot(0, self.close)
        elif pending == "open" and open_path is not None:
            QTimer.singleShot(
                0, lambda path=open_path: self.view_model.dispatch(OpenProject(path))
            )

    def _choose_save_path(self) -> Path | None:
        """Ask where to write a ``.vlt`` project. None if cancelled."""
        suggested = "composition.vlt"
        if self.view_model.state.last_project_path is not None:
            suggested = str(self.view_model.state.last_project_path)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save project",
            suggested,
            f"EklipsComposer project (*{PROJECT_SUFFIX})",
        )
        if not path:
            return None
        out = Path(path)
        if out.suffix.lower() != PROJECT_SUFFIX:
            out = out.with_suffix(PROJECT_SUFFIX)
        return out

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

    def _on_adjust_circle_requested(self, index: int) -> None:
        state = self.view_model.state
        if not (0 <= index < len(state.images)):
            return
        item = state.images[index]
        dialog = AdjustCircleView(
            self._adjust_circle_vm,
            self._adjust_circle_vm.state,
            parent=self,
        )
        self._adjust_circle_vm.dispatch(
            OpenAdjustCircle(index=index, path=item.path, threshold=state.threshold)
        )
        dialog.exec()

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

    def _build_menus(self) -> None:
        """File, View, and Help menus (About lives in the macOS app menu)."""
        menu = self.menuBar().addMenu("&File")
        self._new_action = QAction("New", self)
        self._new_action.setShortcut(QKeySequence.StandardKey.New)
        self._new_action.triggered.connect(self._on_new)
        menu.addAction(self._new_action)
        self._open_action = QAction("Open Project…", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self._on_open)
        menu.addAction(self._open_action)
        menu.addSeparator()
        self._save_action = QAction("Save", self)
        self._save_action.setShortcut(QKeySequence.StandardKey.Save)
        self._save_action.triggered.connect(self._on_save)
        menu.addAction(self._save_action)
        self._save_as_action = QAction("Save As…", self)
        self._save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._save_as_action.triggered.connect(self._on_save_as)
        menu.addAction(self._save_as_action)
        menu.addSeparator()
        self._export_action = QAction("Export…", self)
        self._export_action.triggered.connect(self._on_export)
        menu.addAction(self._export_action)

        view_menu = self.menuBar().addMenu("&View")
        self._fullscreen_action = QAction("Full Screen Preview", self)
        self._fullscreen_action.setShortcut(QKeySequence("F11"))
        self._fullscreen_action.setEnabled(False)
        self._fullscreen_action.triggered.connect(self._on_fullscreen_preview)
        view_menu.addAction(self._fullscreen_action)

        help_menu = self.menuBar().addMenu("&Help")
        self._about_action = QAction("About EklipsComposer", self)
        # AboutRole relocates this item into the macOS application menu
        # (the menu named after the app). Empty Help is then hidden.
        self._about_action.setMenuRole(QAction.MenuRole.AboutRole)
        self._about_action.triggered.connect(self._on_about)
        help_menu.addAction(self._about_action)
        self._licenses_action = QAction("Licenses", self)
        self._licenses_action.triggered.connect(self._on_licenses)
        help_menu.addAction(self._licenses_action)

    def _on_about(self) -> None:
        """Show app credits, version, and the GitHub repository link."""
        show_about_dialog(self)

    def _on_licenses(self) -> None:
        """Show bundled open-source license references."""
        show_licenses_dialog(self)

    def _on_fullscreen_preview(self) -> None:
        """Show (or dismiss) an immersive view of the current composite."""
        if self._fullscreen is not None and self._fullscreen.isVisible():
            minimized = bool(
                self._fullscreen.windowState() & Qt.WindowState.WindowMinimized
            )
            if minimized:
                self._fullscreen.present()
                return
            self._fullscreen.close()
            return
        preview = self.view_model.state.preview_bgr
        if preview is None:
            return
        if self._fullscreen is None:
            self._fullscreen = FullscreenPreview(self)
        self._fullscreen.set_preview(preview, fit=False)  # type: ignore[arg-type]
        self._fullscreen.present()

    def _on_adjust_circle_requested(self, index: int) -> None:
        state = self.view_model.state
        if not (0 <= index < len(state.images)):
            return
        item = state.images[index]
        dialog = AdjustCircleView(
            self._adjust_circle_vm,
            self._adjust_circle_vm.state,
            parent=self,
        )
        # Removed fullscreen enforcement
        self._adjust_circle_vm.dispatch(
            OpenAdjustCircle(index=index, path=item.path, threshold=state.threshold)
        )
        dialog.exec()

    def _on_manual_detection_applied(self, index: int, detection: object) -> None:
        self.view_model.dispatch(ApplyImageDetectionOverride(index=index, detection=detection))
        self.view_model.dispatch(RequestPreview())

    def _on_new(self) -> None:
        if self._import_busy():
            return
        if not self.view_model.state.images:
            return
        if not self._offer_save_before("new"):
            return
        self.view_model.dispatch(ClearImages())

    def _on_open(self) -> None:
        if self._import_busy():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open project",
            "",
            f"EklipsComposer project (*{PROJECT_SUFFIX})",
        )
        if not path:
            return
        self._open_project_path(Path(path))

    def _on_save(self) -> None:
        if self._import_busy():
            return
        path = self.view_model.state.last_project_path
        if path is None or not self.view_model.state.images:
            return
        self.view_model.dispatch(SaveProject(path))

    def _on_save_as(self) -> None:
        if self._import_busy():
            return
        if not self.view_model.state.images:
            return
        out = self._choose_save_path()
        if out is None:
            return
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
        if self.view_model.state.dirty:
            if not self._offer_save_before("open", open_path=path):
                return
        elif self.view_model.state.images:
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
