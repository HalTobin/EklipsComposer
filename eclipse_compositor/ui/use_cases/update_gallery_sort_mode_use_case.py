"""Use case for sorting gallery frames by title or EXIF capture date."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.cv.loading import exif_datetime_taken
from eclipse_compositor.ui.state import GallerySortMode, ImageItem, ScreenState


@dataclass(frozen=True)
class UpdateGallerySortModeUseCase:
    """Reorder the gallery according to the chosen sort key."""

    def invoke(self, state: ScreenState, value: GallerySortMode) -> ScreenState:
        mode = value if isinstance(value, GallerySortMode) else GallerySortMode(value)

        images = state.images
        if mode == GallerySortMode.DATE_TAKEN:
            images = tuple(sorted(images, key=self._date_key))
        else:
            images = tuple(sorted(images, key=lambda item: item.path.name.lower()))

        if images == state.images and mode == state.gallery_sort_mode:
            return state

        selected = state.selected_index
        selected_path: Path | None = None
        if selected is not None and 0 <= selected < len(state.images):
            selected_path = state.images[selected].path

        next_selected: int | None = None
        if selected_path is not None:
            for idx, item in enumerate(images):
                if item.path == selected_path:
                    next_selected = idx
                    break

        return replace(
            state,
            images=images,
            gallery_sort_mode=mode,
            selected_index=next_selected,
        )

    def _date_key(self, item: ImageItem) -> tuple:
        dt = exif_datetime_taken(item.path)
        if dt is not None:
            return (0, dt, item.path.name.lower())
        return (1, item.path.name.lower())
