"""Use case for sorting project media entries by a selected mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eclipse_compositor.ui.state import MediaItem, ProjectSortMode


@dataclass(frozen=True)
class SortProjectMediaUseCase:
    """Sort available media entries according to the chosen project sort mode."""

    def invoke(
        self,
        project_media: tuple[MediaItem, ...],
        sort_mode: str,
    ) -> tuple[MediaItem, ...]:
        mode = ProjectSortMode(sort_mode) if not isinstance(sort_mode, ProjectSortMode) else sort_mode

        if mode == ProjectSortMode.DATE:
            return tuple(sorted(project_media, key=lambda item: (item.date_taken or "", item.title.lower())))

        if mode == ProjectSortMode.FAVORITES_FIRST:
            return tuple(sorted(project_media, key=lambda item: (0 if item.favorite else 1, item.title.lower())))

        return tuple(sorted(project_media, key=lambda item: item.title.lower()))
