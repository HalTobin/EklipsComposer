"""Screen ViewModel — single dispatch entry, unidirectional state flow."""

from __future__ import annotations

import logging
import threading
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal, Slot

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.cv.video import is_supported_video
from eclipse_compositor.project.domain.models import ProjectBlueprint
from eclipse_compositor.ui.actions import (
    ClearImages,
    BlockingJobCancelled,
    CancelJob,
    ExportComposite,
    ExportFailed,
    ExportFinished,
    ExportProgress,
    ImportFailed,
    ImportFinished,
    ImportProgress,
    LoadImages,
    OpenProject,
    OpenProjectFailed,
    OpenProjectFinished,
    OpenProjectProgress,
    PreviewFailed,
    PreviewFinished,
    PreviewProgress,
    RemoveImage,
    ReorderImages,
    RequestPreview,
    ResetColorimetry,
    SaveProject,
    SaveProjectFailed,
    SaveProjectFinished,
    SaveProjectProgress,
    ScreenAction,
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
from eclipse_compositor.ui.project_mapping import blueprint_from_state, state_from_document
from eclipse_compositor.ui.state import (
    DEFAULT_BRIGHTNESS,
    DEFAULT_CONTRAST,
    DEFAULT_GAMMA,
    DEFAULT_MAX_RESOLUTION,
    DEFAULT_SATURATION,
    DEFAULT_TEMPERATURE,
    BlockingJob,
    JobStatus,
    ScreenState,
    SidebarTab,
    default_state,
    enabled_paths,
    native_max_from_shapes,
)
from eclipse_compositor.session_assets import InMemorySessionAssetRepository, SessionAssetRepository
from eclipse_compositor.ui.use_cases import UseCases
from eclipse_compositor.ui.workers import (
    ExportWorker,
    ImportWorker,
    PreviewWorker,
    ProjectOpenResult,
    ProjectOpenWorker,
    ProjectSaveWorker,
    WorkerSignals,
    params_from_state,
)
from eclipse_compositor.cv.pipeline import ComposeParams

logger = logging.getLogger(__name__)


class ScreenViewModel(QObject):
    """Holds ``ScreenState`` and applies actions via ``dispatch``."""

    state_changed = Signal(object)  # ScreenState

    def __init__(
        self,
        parent: QObject | None = None,
        use_cases: UseCases | None = None,
        session_assets: SessionAssetRepository | None = None,
    ) -> None:
        super().__init__(parent)
        self.use_cases = use_cases or UseCases()
        self._state: ScreenState = default_state()
        self._pool = QThreadPool.globalInstance()
        self._assets: SessionAssetRepository = session_assets or InMemorySessionAssetRepository()
        self._clean_blueprint: ProjectBlueprint | None = None
        self._job_cancel: threading.Event | None = None
        self._preview_debounce = QTimer(self)
        self._preview_debounce.setSingleShot(True)
        self._preview_debounce.setInterval(180)
        self._preview_debounce.timeout.connect(self._run_preview)

        # Signals live on the ViewModel (main thread) so QRunnable auto-delete
        # cannot drop completion events and leave Import/Export stuck disabled.
        self._import_signals = WorkerSignals(self)
        self._preview_signals = WorkerSignals(self)
        self._export_signals = WorkerSignals(self)
        self._save_signals = WorkerSignals(self)
        self._open_signals = WorkerSignals(self)
        self._wire_worker_signals()

    def _wire_worker_signals(self) -> None:
        self._import_signals.progress.connect(
            lambda p, m: self.dispatch(ImportProgress(p, m))
        )
        self._import_signals.import_finished.connect(
            lambda items, g: self.dispatch(ImportFinished(tuple(items), g))
        )
        self._import_signals.failed.connect(lambda m: self.dispatch(ImportFailed(m)))

        self._preview_signals.progress.connect(
            lambda p, m: self.dispatch(PreviewProgress(p, m))
        )
        self._preview_signals.preview_finished.connect(
            lambda bgr, g, skipped, flags: self.dispatch(
                PreviewFinished(bgr, g, skipped, flags)
            )
        )
        self._preview_signals.failed.connect(
            lambda m: self.dispatch(
                PreviewFailed(m, self._state._preview_generation)
            )
        )

        self._export_signals.progress.connect(
            lambda p, m: self.dispatch(ExportProgress(p, m))
        )
        self._export_signals.export_finished.connect(
            lambda path, skipped: self.dispatch(ExportFinished(Path(path), skipped))
        )
        self._export_signals.failed.connect(lambda m: self.dispatch(ExportFailed(m)))
        self._export_signals.cancelled.connect(
            lambda token: self.dispatch(BlockingJobCancelled(token))
        )

        self._save_signals.progress.connect(
            lambda p, m: self.dispatch(SaveProjectProgress(p, m))
        )
        self._save_signals.project_saved.connect(
            lambda path: self.dispatch(SaveProjectFinished(Path(path)))
        )
        self._save_signals.failed.connect(lambda m: self.dispatch(SaveProjectFailed(m)))
        self._save_signals.cancelled.connect(
            lambda token: self.dispatch(BlockingJobCancelled(token))
        )

        self._open_signals.progress.connect(
            lambda p, m: self.dispatch(OpenProjectProgress(p, m))
        )
        self._open_signals.project_opened.connect(
            lambda result, g: self.dispatch(OpenProjectFinished(result, g))
        )
        self._open_signals.failed.connect(
            lambda m: self.dispatch(
                OpenProjectFailed(m, self._state._proxy_generation)
            )
        )
        self._open_signals.cancelled.connect(
            lambda token: self.dispatch(BlockingJobCancelled(token))
        )

    @property
    def state(self) -> ScreenState:
        return self._state

    def _is_dirty(self, state: ScreenState) -> bool:
        """True when frames exist and they differ from the last opened/saved project."""
        if not state.images:
            return False
        if self._clean_blueprint is None:
            return True
        return blueprint_from_state(state) != self._clean_blueprint

    def _emit(self, new_state: ScreenState) -> None:
        dirty = self._is_dirty(new_state)
        if new_state.dirty != dirty:
            new_state = replace(new_state, dirty=dirty)
        self._state = new_state
        self.state_changed.emit(new_state)

    def _without_blocking_job(self, state: ScreenState, **changes: object) -> ScreenState:
        """Copy *state* with the lock overlay cleared, plus any extra fields."""
        return replace(
            state,
            blocking_job=None,
            blocking_job_path=None,
            blocking_job_cancelling=False,
            **changes,  # type: ignore[arg-type]
        )

    def _with_selected_frame(
        self,
        state: ScreenState,
        index: int | None,
    ) -> ScreenState:
        """Attach the proxy preview for *index* (or clear if none)."""
        images = state.images
        if index is not None and not (0 <= index < len(images)):
            index = None
        preview = None
        if index is not None:
            preview = self._assets.proxy(images[index].path)
        return replace(
            state,
            selected_index=index,
            selected_preview_bgr=preview,
        )

    def _compose_params(self) -> ComposeParams:
        return params_from_state(self._state)

    @Slot(object)
    def dispatch(self, action: ScreenAction) -> None:
        """Apply *action* using structural pattern matching and emit new state."""
        match action:
            case LoadImages(paths=paths, video_frame_step=video_frame_step):
                if self._io_busy():
                    return
                if not paths:
                    return
                self._start_import(list(paths), video_frame_step=video_frame_step)

            case ClearImages():
                self._assets.clear()
                self._clean_blueprint = None
                self._emit(self.use_cases.clear_images.invoke(self._state))

            case ToggleImage(index=index, enabled=enabled):
                next_state = self.use_cases.toggle_image.invoke(
                    self._state,
                    index,
                    enabled,
                )
                if next_state is not self._state:
                    self._emit(next_state)
                    self._schedule_preview()

            case RemoveImage(indices=indices):
                if not indices:
                    return
                next_state = self.use_cases.remove_image.invoke(self._state, tuple(indices))
                if next_state is self._state:
                    return

                self._assets.discard({item.path for item in next_state.images})

                self._emit(self._with_selected_frame(next_state, next_state.selected_index))
                if not next_state.images:
                    self._assets.clear()
                    self._clean_blueprint = None
                    self._emit(
                        replace(
                            self._state,
                            images=(),
                            preview_bgr=None,
                            proxy_ready=False,
                            native_max_resolution=DEFAULT_MAX_RESOLUTION,
                            status_message="Import eclipse photos to begin, or drop files here.",
                            error_message=None,
                            selected_index=None,
                            selected_preview_bgr=None,
                            import_status=JobStatus.IDLE,
                            export_status=JobStatus.IDLE,
                            preview_status=JobStatus.IDLE,
                        )
                    )
                else:
                    self._schedule_preview()

            case SelectImage(index=index):
                self._emit(self._with_selected_frame(self._state, index))

            case ReorderImages(images=images):
                next_state = self.use_cases.reorder_images.invoke(self._state, images)
                self._emit(self._with_selected_frame(next_state, next_state.selected_index))
                self._schedule_preview()

            case UpdateCropSize(value=value):
                self._emit(self.use_cases.update_layout.invoke(self._state, crop_size=int(value)))
                self._schedule_preview()

            case UpdateSpacing(value=value):
                self._emit(self.use_cases.update_layout.invoke(self._state, spacing=float(value)))
                self._schedule_preview()

            case UpdateLayout(value=value):
                layout = value if isinstance(value, LayoutType) else LayoutType(value)
                self._emit(self.use_cases.update_layout.invoke(self._state, layout=layout))
                self._schedule_preview()

            case UpdateArcAngle(value=value):
                self._emit(self.use_cases.update_layout.invoke(self._state, arc_angle=float(value)))
                self._schedule_preview()

            case UpdateDirection(value=value):
                direction = (
                    value
                    if isinstance(value, LayoutDirection)
                    else LayoutDirection(value)
                )
                self._emit(self.use_cases.update_layout.invoke(self._state, direction=direction))
                self._schedule_preview()

            case UpdateThreshold(value=value):
                self._emit(self.use_cases.update_layout.invoke(self._state, threshold=int(value)))
                self._schedule_preview()

            case UpdateGridColumns(value=value):
                self._emit(self.use_cases.update_layout.invoke(self._state, grid_columns=int(value)))
                self._schedule_preview()

            case UpdateGridRows(value=value):
                self._emit(self.use_cases.update_layout.invoke(self._state, grid_rows=int(value)))
                self._schedule_preview()

            case UpdateZoom(value=value):
                next_state = self.use_cases.update_zoom.invoke(self._state, float(value))
                if next_state is self._state:
                    return
                self._emit(next_state)

            case SelectSidebarTab(value=value):
                tab = value if isinstance(value, SidebarTab) else SidebarTab(value)
                if tab == self._state.sidebar_tab:
                    return
                self._emit(replace(self._state, sidebar_tab=tab))

            case UpdateContrast(value=value):
                self._emit(self.use_cases.update_colorimetry.invoke(self._state, contrast=float(value)))
                self._schedule_preview()

            case UpdateSaturation(value=value):
                self._emit(self.use_cases.update_colorimetry.invoke(self._state, saturation=float(value)))
                self._schedule_preview()

            case UpdateBrightness(value=value):
                self._emit(self.use_cases.update_colorimetry.invoke(self._state, brightness=float(value)))
                self._schedule_preview()

            case UpdateGamma(value=value):
                self._emit(self.use_cases.update_colorimetry.invoke(self._state, gamma=float(value)))
                self._schedule_preview()

            case UpdateTemperature(value=value):
                self._emit(self.use_cases.update_colorimetry.invoke(self._state, temperature=float(value)))
                self._schedule_preview()

            case ResetColorimetry():
                already_default = (
                    abs(self._state.contrast - DEFAULT_CONTRAST) < 1e-6
                    and abs(self._state.saturation - DEFAULT_SATURATION) < 1e-6
                    and abs(self._state.brightness - DEFAULT_BRIGHTNESS) < 1e-6
                    and abs(self._state.gamma - DEFAULT_GAMMA) < 1e-6
                    and abs(self._state.temperature - DEFAULT_TEMPERATURE) < 1e-6
                )
                if already_default:
                    return
                self._emit(self.use_cases.update_colorimetry.invoke(self._state, reset=True))
                self._schedule_preview()

            case UpdateMaskEnabled(value=value):
                enabled = bool(value)
                if enabled == self._state.mask_enabled:
                    return
                self._emit(self.use_cases.update_mask.invoke(self._state, enabled=enabled))
                self._schedule_preview()

            case UpdateMaskSize(value=value):
                self._emit(self.use_cases.update_mask.invoke(self._state, size=float(value)))
                self._schedule_preview()

            case UpdateMaskFeather(value=value):
                self._emit(self.use_cases.update_mask.invoke(self._state, feather=float(value)))
                self._schedule_preview()

            case UpdateMarginLinked(value=value):
                linked = bool(value)
                if linked == self._state.margin_linked:
                    return
                if linked:
                    self._emit(
                        self.use_cases.update_canvas.invoke(
                            self._state,
                            margin_linked=True,
                            margin_y=self._state.margin_x,
                        )
                    )
                    self._schedule_preview()
                else:
                    self._emit(
                        self.use_cases.update_canvas.invoke(self._state, margin_linked=False)
                    )

            case UpdateMarginGlobal(value=value):
                self._emit(
                    self.use_cases.update_canvas.invoke(self._state, margin_global=int(value))
                )
                self._schedule_preview()

            case UpdateMarginX(value=value):
                if self._state.margin_linked:
                    self._emit(
                        self.use_cases.update_canvas.invoke(self._state, margin_global=int(value))
                    )
                else:
                    self._emit(
                        self.use_cases.update_canvas.invoke(self._state, margin_x=int(value))
                    )
                self._schedule_preview()

            case UpdateMarginY(value=value):
                if self._state.margin_linked:
                    self._emit(
                        self.use_cases.update_canvas.invoke(self._state, margin_global=int(value))
                    )
                else:
                    self._emit(
                        self.use_cases.update_canvas.invoke(self._state, margin_y=int(value))
                    )
                self._schedule_preview()

            case RequestPreview():
                self._run_preview()

            case ExportComposite(output_path=output_path):
                if self._io_busy():
                    return
                self._start_export(Path(output_path))

            case SaveProject(output_path=output_path):
                if self._io_busy():
                    return
                self._start_save(Path(output_path))

            case OpenProject(path=path):
                if self._io_busy():
                    return
                self._start_open(Path(path))

            case CancelJob():
                if (
                    self._state.blocking_job is None
                    or self._state.blocking_job_cancelling
                    or self._job_cancel is None
                ):
                    return
                self._job_cancel.set()
                self._emit(
                    replace(
                        self._state,
                        blocking_job_cancelling=True,
                        status_message="Cancelling…",
                    )
                )

            case BlockingJobCancelled(token=token):
                if token is not self._job_cancel:
                    return
                was_open = self._state.blocking_job == BlockingJob.OPEN
                self._job_cancel = None
                if was_open:
                    self._assets.discard_open_staging()
                self._emit(self.use_cases.blocking_job_cancelled.invoke(self._state))

            case ImportProgress(progress=progress, message=message):
                self._emit(
                    self.use_cases.import_progress.invoke(
                        self._state,
                        progress,
                        message,
                    )
                )

            case ImportFinished(images=images, generation=generation):
                if generation != self._state._proxy_generation:
                    return
                native_max = native_max_from_shapes(self._assets.full_shapes)
                next_state = self.use_cases.import_finished.invoke(
                    self._state,
                    images,
                    generation,
                    native_max,
                )
                self._emit(
                    self._with_selected_frame(
                        next_state,
                        next_state.selected_index,
                    )
                )
                self._schedule_preview()

            case ImportFailed(message=message):
                self._emit(self.use_cases.import_failed.invoke(self._state, message))

            case PreviewProgress(progress=progress, message=message):
                self._emit(
                    self.use_cases.preview_progress.invoke(
                        self._state,
                        progress,
                        message,
                    )
                )

            case PreviewFinished(
                preview_bgr=preview_bgr,
                generation=generation,
                skipped=skipped,
                detection_flags=detection_flags,
            ):
                if generation != self._state._preview_generation:
                    return
                self._emit(
                    self.use_cases.preview_finished.invoke(
                        self._state,
                        preview_bgr,
                        generation,
                        skipped,
                        detection_flags,
                    )
                )

            case PreviewFailed(message=message, generation=generation):
                if generation != self._state._preview_generation:
                    return
                self._emit(self.use_cases.preview_failed.invoke(self._state, message))

            case ExportProgress(progress=progress, message=message):
                self._emit(
                    self.use_cases.export_progress.invoke(
                        self._state,
                        progress,
                        message,
                    )
                )

            case ExportFinished(output_path=output_path, skipped=skipped):
                self._job_cancel = None
                self._emit(
                    self._without_blocking_job(
                        self.use_cases.export_finished.invoke(
                            self._state,
                            output_path,
                            skipped,
                        )
                    )
                )

            case ExportFailed(message=message):
                self._job_cancel = None
                self._emit(self.use_cases.export_failed.invoke(self._state, message))

            case SaveProjectProgress(progress=progress, message=message):
                self._emit(
                    self.use_cases.save_project_progress.invoke(
                        self._state,
                        progress,
                        message,
                    )
                )

            case SaveProjectFinished(output_path=output_path):
                saved = self._without_blocking_job(
                    self.use_cases.project_saved.invoke(
                        self._state,
                        output_path,
                    )
                )
                self._job_cancel = None
                self._clean_blueprint = blueprint_from_state(saved)
                self._emit(saved)

            case SaveProjectFailed(message=message):
                self._job_cancel = None
                self._emit(
                    self.use_cases.save_project_failed.invoke(self._state, message)
                )

            case OpenProjectProgress(progress=progress, message=message):
                self._emit(
                    self.use_cases.open_project_progress.invoke(
                        self._state,
                        progress,
                        message,
                    )
                )

            case OpenProjectFinished(result=result, generation=generation):
                if generation != self._state._proxy_generation:
                    return
                if not isinstance(result, ProjectOpenResult):
                    self._assets.discard_open_staging()
                    self._job_cancel = None
                    self._emit(
                        self._without_blocking_job(
                            self._state,
                            import_status=JobStatus.IDLE,
                            error_message="Open returned an unexpected result.",
                            status_message="Open failed.",
                        )
                    )
                    return
                self._adopt_opened_project(result)

            case OpenProjectFailed(message=message, generation=generation):
                if generation != self._state._proxy_generation:
                    return
                self._assets.discard_open_staging()
                self._job_cancel = None
                self._emit(
                    self.use_cases.open_project_failed.invoke(self._state, message)
                )

            case _:
                logger.debug("Unhandled action: %s", type(action).__name__)

    def _schedule_preview(self) -> None:
        """Debounce live preview while sliders / layout controls are moving."""
        if not self._state.images or not self._state.proxy_ready:
            return
        if self._io_busy():
            return
        self._preview_debounce.start()

    def _io_busy(self) -> bool:
        """True when import, open, export, or save is already running."""
        return (
            self._state.import_status == JobStatus.RUNNING
            or self._state.export_status == JobStatus.RUNNING
        )

    def _start_import(self, paths: list[Path], video_frame_step: int = 1) -> None:
        gen = self._state._proxy_generation + 1
        self._emit(
            replace(
                self._state,
                import_status=JobStatus.RUNNING,
                proxy_ready=bool(self._state.images),
                progress=0.0,
                status_message="Importing…",
                error_message=None,
                _proxy_generation=gen,
            )
        )
        frame_dir = None
        if any(is_supported_video(path) for path in paths):
            frame_dir = self._assets.video_frame_dir()
        worker = ImportWorker(
            paths,
            self._assets.proxy_cache,
            self._assets.full_shapes,
            gen,
            self._import_signals,
            frame_dir=frame_dir,
            thumb_dir=self._assets.thumb_dir(),
            video_frame_step=video_frame_step,
        )
        self._pool.start(worker)

    def _start_save(self, output_path: Path) -> None:
        if not self._state.images:
            self.dispatch(SaveProjectFailed("No frames to save."))
            return
        cancel = threading.Event()
        self._job_cancel = cancel
        self._emit(
            replace(
                self._state,
                export_status=JobStatus.RUNNING,
                blocking_job=BlockingJob.SAVE,
                blocking_job_path=output_path,
                blocking_job_cancelling=False,
                progress=0.0,
                status_message="Saving project…",
                error_message=None,
            )
        )
        worker = ProjectSaveWorker(
            blueprint_from_state(self._state),
            output_path,
            self._save_signals,
            cancel,
        )
        self._pool.start(worker)

    def _start_open(self, archive_path: Path) -> None:
        gen = self._state._proxy_generation + 1
        staging_dir = self._assets.begin_open_staging()
        cancel = threading.Event()
        self._job_cancel = cancel
        self._emit(
            replace(
                self._state,
                import_status=JobStatus.RUNNING,
                blocking_job=BlockingJob.OPEN,
                blocking_job_path=archive_path,
                blocking_job_cancelling=False,
                progress=0.0,
                status_message="Opening project…",
                error_message=None,
                _proxy_generation=gen,
            )
        )
        worker = ProjectOpenWorker(
            archive_path,
            staging_dir,
            gen,
            self._open_signals,
            cancel,
        )
        self._pool.start(worker)

    def _adopt_opened_project(self, result: ProjectOpenResult) -> None:
        """Swap caches and restore persistable settings after a successful open."""
        self._assets.commit_open_staging(result.proxy_cache, result.full_shapes)
        native_max = native_max_from_shapes(self._assets.full_shapes)
        restored = state_from_document(
            result.document,
            result.images,
            native_max=native_max,
            project_path=result.project_path,
            proxy_generation=self._state._proxy_generation,
            preview_generation=self._state._preview_generation + 1,
        )
        restored = self.use_cases.project_opened.invoke(
            restored,
            result.project_path,
        )
        selected = restored.selected_index
        adopted = self._with_selected_frame(restored, selected)
        self._job_cancel = None
        self._clean_blueprint = blueprint_from_state(adopted)
        self._emit(adopted)
        self._schedule_preview()

    def _run_preview(self) -> None:
        if not self._state.proxy_ready:
            self._emit(
                replace(
                    self._state,
                    status_message="Import photos before previewing.",
                )
            )
            return
        paths = enabled_paths(self._state)
        if not paths:
            self._emit(
                replace(
                    self._state,
                    preview_bgr=None,
                    status_message="No frames enabled.",
                    preview_status=JobStatus.IDLE,
                )
            )
            return

        gen = self._state._preview_generation + 1
        self._emit(
            replace(
                self._state,
                preview_status=JobStatus.RUNNING,
                _preview_generation=gen,
                status_message="Rendering preview…",
            )
        )
        worker = PreviewWorker(
            paths,
            self._assets.proxy_cache,
            self._assets.full_shapes,
            self._compose_params(),
            gen,
            self._preview_signals,
        )
        self._pool.start(worker)

    def _start_export(self, output_path: Path) -> None:
        paths = enabled_paths(self._state)
        if not paths:
            self.dispatch(ExportFailed("No frames enabled for export."))
            return
        cancel = threading.Event()
        self._job_cancel = cancel
        self._emit(
            replace(
                self._state,
                export_status=JobStatus.RUNNING,
                blocking_job=BlockingJob.EXPORT,
                blocking_job_path=output_path,
                blocking_job_cancelling=False,
                progress=0.0,
                status_message="Exporting…",
                error_message=None,
            )
        )
        worker = ExportWorker(
            paths,
            self._compose_params(),
            output_path,
            self._export_signals,
            cancel,
        )
        self._pool.start(worker)
