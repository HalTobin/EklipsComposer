"""Background QRunnable workers for import, preview, and export.

Heavy OpenCV work never runs on the GUI thread.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.cv.loading import load_image_bgr, make_proxy, write_thumbnail
from eclipse_compositor.cv.pipeline import ComposeParams, compose_sequence, export_composite
from eclipse_compositor.cv.video import is_supported_video, iter_extracted_frames
from eclipse_compositor.ui.state import ImageItem

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
    failed = Signal(str)


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
        h, w = full.shape[:2]
        self.full_shapes[path] = (h, w)
        proxy = make_proxy(full, max_edge=self.max_edge)
        self.proxy_cache[path] = proxy
        thumb_path: str | None = None
        if self.thumb_dir is not None:
            dest = self._thumb_dest(path)
            try:
                write_thumbnail(proxy, dest)
                thumb_path = str(dest)
            except OSError as exc:
                logger.warning("Thumbnail failed for %s: %s", path, exc)
        return ImageItem(path=path, enabled=enabled, thumbnail_path=thumb_path)

    def _thumb_dest(self, path: Path) -> Path:
        """Stable JPEG path under *thumb_dir* for *path*."""
        if self.thumb_dir is None:
            raise RuntimeError("Thumbnail output directory is not set.")
        try:
            key = str(path.resolve())
        except OSError:
            key = str(path)
        digest = hashlib.sha1(key.encode("utf-8", "replace")).hexdigest()[:16]
        return self.thumb_dir / f"{digest}.jpg"

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
        """Map full-res crop/padding onto proxy scale using cached shapes."""
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
        return ComposeParams(
            crop_size=max(32, int(round(self.params.crop_size * scale))),
            spacing=self.params.spacing,
            layout=self.params.layout,
            arc_angle=self.params.arc_angle,
            direction=self.params.direction,
            threshold=self.params.threshold,
            padding=max(8, int(round(self.params.padding * scale))),
            radius_margin=self.params.radius_margin,
            grid_columns=self.params.grid_columns,
            grid_rows=self.params.grid_rows,
        )


class ExportWorker(QRunnable):
    """Full-resolution compose + write to disk."""

    def __init__(
        self,
        paths: list[Path],
        params: ComposeParams,
        output_path: Path,
        signals: WorkerSignals,
    ) -> None:
        super().__init__()
        self.paths = paths
        self.params = params
        self.output_path = output_path
        self.signals = signals
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            self.signals.progress.emit(0.05, "Exporting full-resolution composite…")
            _, _used, skipped = export_composite(
                self.paths, self.params, self.output_path
            )
            self.signals.progress.emit(1.0, f"Saved {self.output_path.name}")
            self.signals.export_finished.emit(self.output_path, tuple(skipped))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Export failed")
            self.signals.failed.emit(str(exc))


def params_from_state(
    crop_size: int,
    spacing: float,
    layout: LayoutType,
    arc_angle: float,
    direction: LayoutDirection,
    threshold: int,
    grid_columns: int = 3,
    grid_rows: int = 2,
) -> ComposeParams:
    """Build ComposeParams from UI scalar fields."""
    return ComposeParams(
        crop_size=crop_size,
        spacing=spacing,
        layout=layout,
        arc_angle=arc_angle,
        direction=direction,
        threshold=threshold,
        padding=40,
        grid_columns=grid_columns,
        grid_rows=grid_rows,
    )
