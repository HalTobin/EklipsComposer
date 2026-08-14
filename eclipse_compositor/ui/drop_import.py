"""Helpers for importing frames via drag-and-drop."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData

from eclipse_compositor.project import is_project_file
from eclipse_compositor.cv.loading import collect_import_paths, is_importable


def mime_has_importable_paths(mime: QMimeData) -> bool:
    """Return True if *mime* contains importable files, folders, or a ``.vlt`` project."""
    if not mime.hasUrls():
        return False
    for url in mime.urls():
        local = url.toLocalFile()
        if not local:
            continue
        path = Path(local)
        if path.is_file() and is_project_file(path):
            return True
        if path.is_dir() or is_importable(path):
            return True
    return False


def paths_from_mime(mime: QMimeData) -> list[Path]:
    """Extract project, image, or video paths from a drop *mime* payload.

    A dropped ``.vlt`` project takes precedence over stills/videos.
    """
    collected: list[Path] = []
    for url in mime.urls():
        local = url.toLocalFile()
        if local:
            collected.append(Path(local))
    for path in collected:
        if path.is_file() and is_project_file(path):
            return [path]
    return collect_import_paths(collected)
