"""Use case for importing and merging gallery images."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ImageItem, ScreenState


@dataclass(frozen=True)
class LoadImagesUseCase:
    """Append unique imported frames while preserving the current selection."""

    def invoke(self, state: ScreenState, images: tuple[ImageItem, ...]) -> ScreenState:
        if not images:
            return state

        merged: list[ImageItem] = list(state.images)
        existing_paths = {item.path for item in merged}
        merged.extend(item for item in images if item.path not in existing_paths)

        next_selected = state.selected_index
        if next_selected is None and merged:
            next_selected = 0
        elif next_selected is not None and next_selected >= len(merged):
            next_selected = max(0, len(merged) - 1)

        return replace(
            state,
            images=tuple(merged),
            selected_index=next_selected,
            proxy_ready=bool(merged),
            status_message="Images imported.",
            error_message=None,
        )
