"""Background QRunnable workers for import, preview, export, and projects.

Heavy OpenCV work never runs on the GUI thread.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from eclipse_compositor.cv.detection import DiscDetection
from eclipse_compositor.cv.loading import load_image_bgr, make_proxy, write_thumbnail
from eclipse_compositor.cv.pipeline import ComposeParams, compose_sequence, export_composite
from eclipse_compositor.cv.video import is_supported_video, iter_extracted_frames
from eclipse_compositor.project import ProjectBlueprint, ProjectDocument, ManualDetection, default_project_service
from eclipse_compositor.ui.state import ImageItem, ScreenState

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Qt signals emitted by background workers (must live on QObject).

    Own these on the ViewModel (main thread) so queued emissions are not lost
    when a QRunnable is reclaimed by the thread pool.
    """

    progress = Signal(float, str)
    import_finished = Signal(object, int)  # list[ImageItem], generation
    preview_finished = Signal(object, int, object, object)  # bgr, gen, skipped, flags
    export_finished = Signal(object, object)  # Path, skipped
    project_saved = Signal(object)  # Path
    project_opened = Signal(object, int)  # ProjectOpenResult, generation
    failed = Signal(str)
    cancelled = Signal(object)  # threading.Event token for the stopped job


def cache_imported_frame(
    path: Path,
    full: np.ndarray,
    proxy_cache: dict[Path, np.ndarray],
    full_shapes: dict[Path, tuple[int, int]],
    thumb_dir: Path | None,
    *,
    enabled: bool = True,
    favorite: bool = False,
    manual_detection: object | None = None,
    max_edge: int = 1080,
) -> ImageItem:
    """Store proxy + native shape for one still and return its gallery item."""
    h, w = full.shape[:2]
    full_shapes[path] = (h, w)
    proxy = make_proxy(full, max_edge=max_edge)
    proxy_cache[path] = proxy
    thumb_path: str | None = None
    if thumb_dir is not None:
        dest = _thumb_dest(thumb_dir, path)
        try:
            write_thumbnail(proxy, dest)
            thumb_path = str(dest)
        except OSError as exc:
            logger.warning("Thumbnail failed for %s: %s", path, exc)
    if isinstance(manual_detection, ManualDetection):
        manual_detection = DiscDetection(
            center=manual_detection.center,
            radius=manual_detection.radius,
            area=manual_detection.area,
            confidence=manual_detection.confidence,
        )
    return ImageItem(
        path=path,
        enabled=enabled,
        favorite=favorite,
        manual_detection=manual_detection,
        thumbnail_path=thumb_path,
    )


def _thumb_dest(thumb_dir: Path, path: Path) -> Path:
    """Stable JPEG path under *thumb_dir* for *path*."""
    try:
        key = str(path.resolve())
    except OSError:
        key = str(path)
    digest = hashlib.sha1(key.encode("utf-8", "replace")).hexdigest()[:16]
    return thumb_dir / f"{digest}.jpg"


@dataclass
class ProjectOpenResult:
    """Staging payload from ``ProjectOpenWorker`` (swapped in on the main thread)."""

    document: ProjectDocument
    images: tuple[ImageItem, ...]
    proxy_cache: dict[Path, np.ndarray]
    full_shapes: dict[Path, tuple[int, int]]
    extract_dir: Path
    project_path: Path


class ImportWorker(QRunnable):
    """Load images in the given order and build proxy cache entries."""

    def __init__(
        self,
        paths: list[Path],
        proxy_cache: dict[Path, np.ndarray],
        full_shapes: dict[Path, tuple[int, int]],
        generation: int,
        signals: WorkerSignals,
        max_edge: int = 1080,
        frame_dir: Path | None = None,
        thumb_dir: Path | None = None,
        video_frame_step: int = 1,
    ) -> None:
        super().__init__()
        self.paths = paths
        self.proxy_cache = proxy_cache
        self.full_shapes = full_shapes
        self.generation = generation
        self.signals = signals
        self.max_edge = max_edge
        self.frame_dir = frame_dir
        self.thumb_dir = thumb_dir
        self.video_frame_step = max(1, int(video_frame_step))
        self.setAutoDelete(True)

    def _cache_frame(
        self, path: Path, full: np.ndarray, *, enabled: bool = True
    ) -> ImageItem:
        """Store proxy + native shape for one still and return its gallery item."""
        return cache_imported_frame(
            path,
            full,
            self.proxy_cache,
            self.full_shapes,
            self.thumb_dir,
            enabled=enabled,
            max_edge=self.max_edge,
        )

    def _unique_frame_dir(self, video: Path) -> Path:
        """Return a fresh subdirectory under *frame_dir* for *video* stills."""
        if self.frame_dir is None:
            raise RuntimeError("Video import requires a frame output directory.")
        stem = video.stem or "video"
        dest = self.frame_dir / stem
        suffix = 2
        while dest.exists():
            dest = self.frame_dir / f"{stem}_{suffix}"
            suffix += 1
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    @Slot()
    def run(self) -> None:
        try:
            # Preserve the order the user selected in the file dialog.
            ordered = list(self.paths)
            items: list[ImageItem] = []
            total = max(1, len(ordered))
            for i, path in enumerate(ordered):
                try:
                    if is_supported_video(path):
                        dest = self._unique_frame_dir(path)
                        extracted = 0

                        def _on_frame(
                            count: int,
                            name: str = path.name,
                            index: int = i,
                        ) -> None:
                            self.signals.progress.emit(
                                (index + 0.5) / total,
                                f"Extracting {name} ({count} frames)…",
                            )

                        for still, bgr in iter_extracted_frames(
                            path, dest, progress=_on_frame
                        ):
                            enabled = extracted % self.video_frame_step == 0
                            items.append(
                                self._cache_frame(still, bgr, enabled=enabled)
                            )
                            extracted += 1
                        if extracted == 0:
                            logger.warning("No frames extracted from %s", path)
                        continue

                    self.signals.progress.emit((i + 1) / total, f"Loading {path.name}…")
                    full = load_image_bgr(path)
                    items.append(self._cache_frame(path, full))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to import %s: %s", path, exc)
            self.signals.import_finished.emit(items, self.generation)
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(str(exc))


class PreviewWorker(QRunnable):
    """Compose a preview from downscaled proxies."""

    def __init__(
        self,
        paths: list[Path],
        proxy_cache: dict[Path, np.ndarray],
        full_shapes: dict[Path, tuple[int, int]],
        params: ComposeParams,
        generation: int,
        signals: WorkerSignals,
    ) -> None:
        super().__init__()
        self.paths = paths
        self.proxy_cache = proxy_cache
        self.full_shapes = full_shapes
        self.params = params
        self.generation = generation
        self.signals = signals
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            self.signals.progress.emit(0.1, "Compositing preview…")
            proxy_params = self._scaled_params()
            images = {p: self.proxy_cache[p] for p in self.paths if p in self.proxy_cache}
            composite, used, skipped = compose_sequence(
                self.paths, proxy_params, images=images
            )
            flags = tuple((p, p in used) for p in self.paths)
            self.signals.progress.emit(1.0, "Preview ready.")
            self.signals.preview_finished.emit(
                composite, self.generation, tuple(skipped), flags
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Preview failed")
            self.signals.failed.emit(str(exc))

    def _scaled_params(self) -> ComposeParams:
        """Map full-res crop and canvas margins onto proxy scale."""
        if not self.paths:
            return self.params
        first = self.paths[0]
        proxy = self.proxy_cache.get(first)
        full_shape = self.full_shapes.get(first)
        if proxy is None:
            return self.params
        if full_shape is not None:
            full_h, full_w = full_shape
            proxy_h, proxy_w = proxy.shape[:2]
            scale = min(proxy_w / max(full_w, 1), proxy_h / max(full_h, 1))
        else:
            scale = max(proxy.shape[:2]) / 4000.0
        return replace(
            self.params,
            crop_size=max(32, int(round(self.params.crop_size * scale))),
            margin_x=_scale_margin(self.params.margin_x, scale),
            margin_y=_scale_margin(self.params.margin_y, scale),
        )


class ExportWorker(QRunnable):
    """Full-resolution compose + write to disk."""

    def __init__(
        self,
        paths: list[Path],
        params: ComposeParams,
        output_path: Path,
        signals: WorkerSignals,
        cancel: threading.Event,
    ) -> None:
        super().__init__()
        self.paths = paths
        self.params = params
        self.output_path = output_path
        self.signals = signals
        self.cancel = cancel
        self.setAutoDelete(True)

    def _progress(self, fraction: float, message: str) -> None:
        if self.cancel.is_set():
            raise InterruptedError("Cancelled")
        self.signals.progress.emit(fraction, message)

    @Slot()
    def run(self) -> None:
        try:
            self._progress(0.02, "Exporting full-resolution composite…")
            _, _used, skipped = export_composite(
                self.paths,
                self.params,
                self.output_path,
                on_progress=self._progress,
                should_cancel=self.cancel.is_set,
            )
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            self.signals.export_finished.emit(self.output_path, tuple(skipped))
        except InterruptedError:
            self.signals.cancelled.emit(self.cancel)
        except Exception as exc:  # noqa: BLE001
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            logger.exception("Export failed")
            self.signals.failed.emit(str(exc))


class ProjectSaveWorker(QRunnable):
    """Pack the current composition into a ``.vlt`` archive."""

    def __init__(
        self,
        blueprint: ProjectBlueprint,
        output_path: Path,
        signals: WorkerSignals,
        cancel: threading.Event,
    ) -> None:
        super().__init__()
        self.blueprint = blueprint
        self.output_path = output_path
        self.signals = signals
        self.cancel = cancel
        self.setAutoDelete(True)

    def _progress(self, fraction: float, message: str) -> None:
        if self.cancel.is_set():
            raise InterruptedError("Cancelled")
        self.signals.progress.emit(fraction, message)

    @Slot()
    def run(self) -> None:
        try:
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            service = default_project_service()
            saved = service.save(
                self.blueprint,
                self.output_path,
                progress=self._progress,
            )
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            self.signals.project_saved.emit(saved)
        except InterruptedError:
            self.signals.cancelled.emit(self.cancel)
        except Exception as exc:  # noqa: BLE001
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            logger.exception("Save project failed")
            self.signals.failed.emit(str(exc))


class ProjectOpenWorker(QRunnable):
    """Extract a ``.vlt`` archive and build proxy cache entries."""

    def __init__(
        self,
        archive_path: Path,
        extract_dir: Path,
        generation: int,
        signals: WorkerSignals,
        cancel: threading.Event,
        max_edge: int = 1080,
    ) -> None:
        super().__init__()
        self.archive_path = archive_path
        self.extract_dir = extract_dir
        self.generation = generation
        self.signals = signals
        self.cancel = cancel
        self.max_edge = max_edge
        self.setAutoDelete(True)

    def _progress(self, fraction: float, message: str) -> None:
        if self.cancel.is_set():
            raise InterruptedError("Cancelled")
        self.signals.progress.emit(fraction, message)

    @Slot()
    def run(self) -> None:
        try:
            self._progress(0.02, "Opening project…")
            service = default_project_service()
            loaded = service.open(self.archive_path, self.extract_dir)
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            proxy_cache: dict[Path, np.ndarray] = {}
            full_shapes: dict[Path, tuple[int, int]] = {}
            thumb_dir = self.extract_dir / "thumbs"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            items: list[ImageItem] = []
            total = max(1, len(loaded.frame_paths))
            for i, (record, path) in enumerate(
                zip(loaded.document.frames, loaded.frame_paths, strict=True)
            ):
                self._progress(
                    0.1 + 0.85 * ((i + 1) / total),
                    f"Loading {path.name}…",
                )
                full = load_image_bgr(path)
                items.append(
                    cache_imported_frame(
                        path,
                        full,
                        proxy_cache,
                        full_shapes,
                        thumb_dir,
                        enabled=record.enabled,
                        favorite=record.favorite,
                        manual_detection=record.manual_detection,
                        max_edge=self.max_edge,
                    )
                )
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            result = ProjectOpenResult(
                document=loaded.document,
                images=tuple(items),
                proxy_cache=proxy_cache,
                full_shapes=full_shapes,
                extract_dir=self.extract_dir,
                project_path=self.archive_path,
            )
            self._progress(1.0, "Project loaded.")
            self.signals.project_opened.emit(result, self.generation)
        except InterruptedError:
            self.signals.cancelled.emit(self.cancel)
        except Exception as exc:  # noqa: BLE001
            if self.cancel.is_set():
                self.signals.cancelled.emit(self.cancel)
                return
            logger.exception("Open project failed")
            self.signals.failed.emit(str(exc))


def _scale_margin(value: int, scale: float) -> int:
    """Map a full-res canvas margin onto proxy scale, preserving sign."""
    if value == 0:
        return 0
    scaled = int(round(value * scale))
    if scaled == 0:
        return 1 if value > 0 else -1
    return scaled


def params_from_state(state: ScreenState) -> ComposeParams:
    """Build ComposeParams from the current screen state."""
    return ComposeParams(
        crop_size=state.crop_size,
        spacing=state.spacing,
        layout=state.layout,
        arc_angle=state.arc_angle,
        direction=state.direction,
        threshold=state.threshold,
        margin_x=state.margin_x,
        margin_y=state.margin_y,
        grid_columns=state.grid_columns,
        grid_rows=state.grid_rows,
        contrast=state.contrast,
        saturation=state.saturation,
        brightness=state.brightness,
        gamma=state.gamma,
        temperature=state.temperature,
        mask_enabled=state.mask_enabled,
        mask_size=state.mask_size,
        mask_feather=state.mask_feather,
        manual_detections={
            item.path: item.manual_detection
            for item in state.images
            if item.manual_detection is not None
        },
    )
