"""Helpers for importing frames via drag-and-drop."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData

from eclipse_compositor.cv.loading import collect_import_paths, is_importable


def mime_has_importable_paths(mime: QMimeData) -> bool:
    """Return True if *mime* contains local image/video files or folders."""
    if not mime.hasUrls():
        return False
    for url in mime.urls():
        local = url.toLocalFile()
        if not local:
            continue
        path = Path(local)
        if path.is_dir() or is_importable(path):
            return True
    return False


def paths_from_mime(mime: QMimeData) -> list[Path]:
    """Extract supported image and video paths from a drop *mime* payload."""
    candidates: list[Path] = []
    for url in mime.urls():
        local = url.toLocalFile()
        if local:
            candidates.append(Path(local))
    return collect_import_paths(candidates)
