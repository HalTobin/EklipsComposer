"""Use case for toggling a project media item's favorite flag by filepath."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import MediaItem


@dataclass(frozen=True)
class ToggleProjectFavoriteUseCase:
    """Toggle favorite state for one project media item by file path."""

    def invoke(
        self,
        project_media: tuple[MediaItem, ...],
        filepath: str,
        favorite: bool,
    ) -> tuple[MediaItem, ...]:
        target_path = Path(filepath)
        updated: list[MediaItem] = []
        changed = False
        for item in project_media:
            if item.path == target_path:
                changed = changed or item.favorite != favorite
                updated.append(replace(item, favorite=favorite))
            else:
                updated.append(item)

        if not changed:
            return project_media

        return tuple(updated)
