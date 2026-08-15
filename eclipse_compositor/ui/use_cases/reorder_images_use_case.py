"""Use case for reordering the gallery while preserving the selected item."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import ImageItem, ScreenState


@dataclass(frozen=True)
class ReorderImagesUseCase:
    """Re-sort the gallery while preserving the user's current selection."""

    def invoke(self, state: ScreenState, images: tuple[ImageItem, ...]) -> ScreenState:
        if not images:
            return replace(state, images=(), selected_index=None)

        selected_index = state.selected_index
        selected_path: Path | None = None
        if selected_index is not None and 0 <= selected_index < len(state.images):
            selected_path = state.images[selected_index].path

        next_selected: int | None = None
        if selected_path is not None:
            for idx, item in enumerate(images):
                if item.path == selected_path:
                    next_selected = idx
                    break

        if next_selected is None:
            next_selected = 0 if state.images else None

        return replace(
            state,
            images=images,
            selected_index=next_selected,
        )
