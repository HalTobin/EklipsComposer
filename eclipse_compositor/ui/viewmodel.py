"""Screen ViewModel — single dispatch entry, unidirectional state flow."""

from __future__ import annotations

import logging
import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal, Slot

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.cv.video import is_supported_video
from eclipse_compositor.ui.actions import (
    ClearImages,
    ExportComposite,
    ExportFailed,
    ExportFinished,
    ExportProgress,
    ImportFailed,
    ImportFinished,
    ImportProgress,
    LoadImages,
    PreviewFailed,
    PreviewFinished,
    PreviewProgress,
    ReorderImages,
    RequestPreview,
    ScreenAction,
    SelectImage,
    ToggleImage,
    UpdateArcAngle,
    UpdateCropSize,
    UpdateDirection,
    UpdateGridColumns,
    UpdateGridRows,
    UpdateLayout,
    UpdateSpacing,
    UpdateThreshold,
    UpdateZoom,
)
from eclipse_compositor.ui.state import (
    DEFAULT_MAX_RESOLUTION,
    MIN_RESOLUTION,
    JobStatus,
    ScreenState,
    default_state,
    enabled_paths,
    native_max_from_shapes,
)
from eclipse_compositor.ui.workers import (
    ExportWorker,
    ImportWorker,
    PreviewWorker,
    WorkerSignals,
    params_from_state,
)
from eclipse_compositor.cv.pipeline import ComposeParams

logger = logging.getLogger(__name__)


class ScreenViewModel(QObject):
    """Holds ``ScreenState`` and applies actions via ``dispatch``."""

    state_changed = Signal(object)  # ScreenState

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state: ScreenState = default_state()
        self._pool = QThreadPool.globalInstance()
        self._proxy_cache: dict[Path, np.ndarray] = {}
        self._full_shapes: dict[Path, tuple[int, int]] = {}
        self._video_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._thumb_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._preview_debounce = QTimer(self)
        self._preview_debounce.setSingleShot(True)
        self._preview_debounce.setInterval(180)
        self._preview_debounce.timeout.connect(self._run_preview)

        # Signals live on the ViewModel (main thread) so QRunnable auto-delete
        # cannot drop completion events and leave Import/Export stuck disabled.
        self._import_signals = WorkerSignals(self)
        self._preview_signals = WorkerSignals(self)
        self._export_signals = WorkerSignals(self)
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

    @property
    def state(self) -> ScreenState:
        return self._state

    def _emit(self, new_state: ScreenState) -> None:
        self._state = new_state
        self.state_changed.emit(new_state)

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
            preview = self._proxy_cache.get(images[index].path)
        return replace(
            state,
            selected_index=index,
            selected_preview_bgr=preview,
        )

    def _compose_params(self) -> ComposeParams:
        return params_from_state(
            self._state.crop_size,
            self._state.spacing,
            self._state.layout,
            self._state.arc_angle,
            self._state.direction,
            self._state.threshold,
            self._state.grid_columns,
            self._state.grid_rows,
        )

    @Slot(object)
    def dispatch(self, action: ScreenAction) -> None:
        """Apply *action* using structural pattern matching and emit new state."""
        match action:
            case LoadImages(paths=paths, video_frame_step=video_frame_step):
                if (
                    self._state.import_status == JobStatus.RUNNING
                    or self._state.export_status == JobStatus.RUNNING
                ):
                    return
                if not paths:
                    return
                self._start_import(list(paths), video_frame_step=video_frame_step)

            case ClearImages():
                self._proxy_cache.clear()
                self._full_shapes.clear()
                self._clear_video_tmpdir()
                self._clear_thumb_tmpdir()
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

            case ToggleImage(index=index, enabled=enabled):
                images = list(self._state.images)
                if 0 <= index < len(images):
                    images[index] = replace(images[index], enabled=enabled)
                    self._emit(replace(self._state, images=tuple(images)))
                    self._schedule_preview()

            case SelectImage(index=index):
                self._emit(self._with_selected_frame(self._state, index))

            case ReorderImages(images=images):
                selected_path: Path | None = None
                sel = self._state.selected_index
                if sel is not None and 0 <= sel < len(self._state.images):
                    selected_path = self._state.images[sel].path
                new_index = None
                if selected_path is not None:
                    for i, item in enumerate(images):
                        if item.path == selected_path:
                            new_index = i
                            break
                self._emit(
                    self._with_selected_frame(
                        replace(self._state, images=images), new_index
                    )
                )
                self._schedule_preview()

            case UpdateCropSize(value=value):
                capped = max(
                    MIN_RESOLUTION,
                    min(int(value), self._state.native_max_resolution),
                )
                self._emit(replace(self._state, crop_size=capped))
                self._schedule_preview()

            case UpdateSpacing(value=value):
                self._emit(replace(self._state, spacing=float(value)))
                self._schedule_preview()

            case UpdateLayout(value=value):
                layout = value if isinstance(value, LayoutType) else LayoutType(value)
                self._emit(replace(self._state, layout=layout))
                self._schedule_preview()

            case UpdateArcAngle(value=value):
                angle = max(-180.0, min(180.0, float(value)))
                self._emit(replace(self._state, arc_angle=angle))
                self._schedule_preview()

            case UpdateDirection(value=value):
                direction = (
                    value
                    if isinstance(value, LayoutDirection)
                    else LayoutDirection(value)
                )
                self._emit(replace(self._state, direction=direction))
                self._schedule_preview()

            case UpdateThreshold(value=value):
                self._emit(replace(self._state, threshold=int(value)))
                self._schedule_preview()

            case UpdateGridColumns(value=value):
                self._emit(replace(self._state, grid_columns=max(1, int(value))))
                self._schedule_preview()

            case UpdateGridRows(value=value):
                self._emit(replace(self._state, grid_rows=max(1, int(value))))
                self._schedule_preview()

            case UpdateZoom(value=value):
                # Allow very small fit-to-view scales for large composites.
                zoom = max(0.01, min(8.0, float(value)))
                if abs(zoom - self._state.zoom) < 1e-6:
                    return
                self._emit(replace(self._state, zoom=zoom))

            case RequestPreview():
                self._run_preview()

            case ExportComposite(output_path=output_path):
                self._start_export(Path(output_path))

            case ImportProgress(progress=progress, message=message):
                self._emit(
                    replace(
                        self._state,
                        progress=progress,
                        status_message=message,
                        import_status=JobStatus.RUNNING,
                    )
                )

            case ImportFinished(images=images, generation=generation):
                if generation != self._state._proxy_generation:
                    return
                existing = list(self._state.images)
                existing_paths = {item.path for item in existing}
                merged = existing + [
                    img for img in images if img.path not in existing_paths
                ]
                native_max = native_max_from_shapes(self._full_shapes)
                crop_size = min(self._state.crop_size, native_max)
                merged_tuple = tuple(merged)
                selected = self._state.selected_index
                if selected is None and merged_tuple:
                    selected = 0
                elif selected is not None and selected >= len(merged_tuple):
                    selected = 0 if merged_tuple else None
                self._emit(
                    self._with_selected_frame(
                        replace(
                            self._state,
                            images=merged_tuple,
                            import_status=JobStatus.IDLE,
                            proxy_ready=True,
                            native_max_resolution=native_max,
                            crop_size=crop_size,
                            progress=1.0,
                            status_message=(
                                f"Imported {len(images)} frame(s). "
                                "Preview updates live as you adjust settings."
                            ),
                            error_message=None,
                        ),
                        selected,
                    )
                )
                self._schedule_preview()

            case ImportFailed(message=message):
                self._emit(
                    replace(
                        self._state,
                        import_status=JobStatus.IDLE,
                        error_message=message,
                        status_message="Import failed.",
                    )
                )

            case PreviewProgress(progress=progress, message=message):
                self._emit(
                    replace(
                        self._state,
                        progress=progress,
                        status_message=message,
                        preview_status=JobStatus.RUNNING,
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
                flag_map = dict(detection_flags)
                updated = tuple(
                    replace(item, detection_ok=flag_map.get(item.path))
                    for item in self._state.images
                )
                skip_note = (
                    f" Skipped {len(skipped)} (no disc)." if skipped else ""
                )
                self._emit(
                    replace(
                        self._state,
                        images=updated,
                        preview_bgr=preview_bgr,
                        preview_status=JobStatus.IDLE,
                        progress=1.0,
                        status_message=f"Preview updated.{skip_note}",
                        error_message=None,
                    )
                )

            case PreviewFailed(message=message, generation=generation):
                if generation != self._state._preview_generation:
                    return
                self._emit(
                    replace(
                        self._state,
                        preview_status=JobStatus.IDLE,
                        error_message=message,
                        status_message="Preview failed.",
                    )
                )

            case ExportProgress(progress=progress, message=message):
                self._emit(
                    replace(
                        self._state,
                        progress=progress,
                        status_message=message,
                        export_status=JobStatus.RUNNING,
                    )
                )

            case ExportFinished(output_path=output_path, skipped=skipped):
                skip_note = (
                    f" Skipped {len(skipped)} frame(s)." if skipped else ""
                )
                self._emit(
                    replace(
                        self._state,
                        export_status=JobStatus.IDLE,
                        last_export_path=output_path,
                        progress=1.0,
                        status_message=f"Exported to {output_path}.{skip_note}",
                        error_message=None,
                    )
                )

            case ExportFailed(message=message):
                self._emit(
                    replace(
                        self._state,
                        export_status=JobStatus.IDLE,
                        error_message=message,
                        status_message="Export failed.",
                    )
                )

            case _:
                logger.debug("Unhandled action: %s", type(action).__name__)

    def _schedule_preview(self) -> None:
        """Debounce live preview while sliders / layout controls are moving."""
        if not self._state.images or not self._state.proxy_ready:
            return
        if self._state.import_status == JobStatus.RUNNING:
            return
        if self._state.export_status == JobStatus.RUNNING:
            return
        self._preview_debounce.start()

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
            frame_dir = self._ensure_video_tmpdir()
        worker = ImportWorker(
            paths,
            self._proxy_cache,
            self._full_shapes,
            gen,
            self._import_signals,
            frame_dir=frame_dir,
            thumb_dir=self._ensure_thumb_tmpdir(),
            video_frame_step=video_frame_step,
        )
        self._pool.start(worker)

    def _ensure_video_tmpdir(self) -> Path:
        """Return the directory used to persist extracted video stills."""
        if self._video_tmpdir is None:
            self._video_tmpdir = tempfile.TemporaryDirectory(
                prefix="vultureklips_frames_"
            )
        return Path(self._video_tmpdir.name)

    def _ensure_thumb_tmpdir(self) -> Path:
        """Return the directory used to persist gallery list thumbnails."""
        if self._thumb_tmpdir is None:
            self._thumb_tmpdir = tempfile.TemporaryDirectory(
                prefix="vultureklips_thumbs_"
            )
        return Path(self._thumb_tmpdir.name)

    def _clear_video_tmpdir(self) -> None:
        """Delete extracted video stills (called when the gallery is cleared)."""
        if self._video_tmpdir is None:
            return
        try:
            self._video_tmpdir.cleanup()
        except OSError as exc:
            logger.warning("Failed to clean up extracted video frames: %s", exc)
        self._video_tmpdir = None

    def _clear_thumb_tmpdir(self) -> None:
        """Delete gallery thumbnails (called when the gallery is cleared)."""
        if self._thumb_tmpdir is None:
            return
        try:
            self._thumb_tmpdir.cleanup()
        except OSError as exc:
            logger.warning("Failed to clean up frame thumbnails: %s", exc)
        self._thumb_tmpdir = None

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
            self._proxy_cache,
            self._full_shapes,
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
        self._emit(
            replace(
                self._state,
                export_status=JobStatus.RUNNING,
                progress=0.0,
                status_message="Exporting…",
                error_message=None,
            )
        )
        worker = ExportWorker(
            paths, self._compose_params(), output_path, self._export_signals
        )
        self._pool.start(worker)
