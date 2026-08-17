"""In-memory ``SessionAssetRepository`` backed by ``tempfile`` scratch dirs."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np

logger = logging.getLogger(__name__)


class InMemorySessionAssetRepository:
    """Session-scoped proxy/shape cache plus extracted-file temp dirs.

    Not thread-safe beyond what CPython's GIL gives plain dict writes; this
    matches how import/preview/open workers already mutate ``proxy_cache``
    and ``full_shapes`` from a background ``QThreadPool`` thread.
    """

    def __init__(self) -> None:
        self._proxy_cache: dict[Path, np.ndarray] = {}
        self._full_shapes: dict[Path, tuple[int, int]] = {}
        self._video_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._thumb_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._project_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self._open_staging: tempfile.TemporaryDirectory[str] | None = None

    @property
    def proxy_cache(self) -> dict[Path, np.ndarray]:
        return self._proxy_cache

    @property
    def full_shapes(self) -> dict[Path, tuple[int, int]]:
        return self._full_shapes

    def proxy(self, path: Path) -> np.ndarray | None:
        return self._proxy_cache.get(path)

    def discard(self, keep: Iterable[Path]) -> None:
        keep_set = set(keep)
        for path in list(self._proxy_cache):
            if path not in keep_set:
                self._proxy_cache.pop(path, None)
        for path in list(self._full_shapes):
            if path not in keep_set:
                self._full_shapes.pop(path, None)

    def clear(self) -> None:
        self._proxy_cache.clear()
        self._full_shapes.clear()
        self._clear_tmpdir("_video_tmpdir", "extracted video frames")
        self._clear_tmpdir("_thumb_tmpdir", "frame thumbnails")
        self._clear_tmpdir("_project_tmpdir", "opened project files")
        self._clear_tmpdir("_open_staging", "project staging files")

    def video_frame_dir(self) -> Path:
        if self._video_tmpdir is None:
            self._video_tmpdir = tempfile.TemporaryDirectory(
                prefix="eklipscomposer_frames_"
            )
        return Path(self._video_tmpdir.name)

    def thumb_dir(self) -> Path:
        if self._thumb_tmpdir is None:
            self._thumb_tmpdir = tempfile.TemporaryDirectory(
                prefix="eklipscomposer_thumbs_"
            )
        return Path(self._thumb_tmpdir.name)

    def begin_open_staging(self) -> Path:
        self.discard_open_staging()
        self._open_staging = tempfile.TemporaryDirectory(
            prefix="eklipscomposer_project_"
        )
        return Path(self._open_staging.name)

    def commit_open_staging(
        self,
        proxy_cache: dict[Path, np.ndarray],
        full_shapes: dict[Path, tuple[int, int]],
    ) -> None:
        self._clear_tmpdir("_video_tmpdir", "extracted video frames")
        self._clear_tmpdir("_thumb_tmpdir", "frame thumbnails")
        self._clear_tmpdir("_project_tmpdir", "opened project files")
        self._project_tmpdir = self._open_staging
        self._open_staging = None
        self._proxy_cache = proxy_cache
        self._full_shapes = full_shapes

    def discard_open_staging(self) -> None:
        self._clear_tmpdir("_open_staging", "project staging files")

    def close(self) -> None:
        self._clear_tmpdir("_video_tmpdir", "extracted video frames")
        self._clear_tmpdir("_thumb_tmpdir", "frame thumbnails")
        self._clear_tmpdir("_project_tmpdir", "opened project files")
        self._clear_tmpdir("_open_staging", "project staging files")

    def _clear_tmpdir(self, attr: str, description: str) -> None:
        tmpdir = getattr(self, attr)
        if tmpdir is None:
            return
        try:
            tmpdir.cleanup()
        except OSError as exc:
            logger.warning("Failed to clean up %s: %s", description, exc)
        setattr(self, attr, None)
