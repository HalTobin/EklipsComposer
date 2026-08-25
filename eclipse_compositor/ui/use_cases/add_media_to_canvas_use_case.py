"""Use case for adding a project media item to the canvas."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import uuid

from eclipse_compositor.ui.state import CanvasItem, MediaItem


@dataclass(frozen=True)
class AddMediaToCanvasUseCase:
    """Append a project media item to the canvas list by filepath."""

    def invoke(
        self,
        project_media: tuple[MediaItem, ...],
        canvas_media: tuple[CanvasItem, ...],
        filepath: str,
    ) -> tuple[CanvasItem, ...]:
        target_path = Path(filepath)
        source = next((item for item in project_media if item.path == target_path), None)
        if source is None:
            return canvas_media

        new_item = CanvasItem(
            id=str(uuid.uuid4()),
            path=source.path,
            title=source.title,
            favorite=source.favorite,
            thumbnail_path=source.thumbnail_path,
        )
        return tuple((*canvas_media, new_item))
