"""Use case for removing frames from the gallery while preserving selection."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class RemoveImageUseCase:
    """Remove one or more gallery images and keep the selection consistent."""

    def invoke(self, state: ScreenState, indices: tuple[int, ...]) -> ScreenState:
        if not indices:
            return state

        rows = sorted({int(i) for i in indices if isinstance(i, int)})
        if not rows:
            return state

        images = list(state.images)
        valid_rows = sorted(i for i in rows if 0 <= i < len(images))
        if not valid_rows:
            return state

        removed_paths = {images[i].path for i in valid_rows}
        for idx in reversed(valid_rows):
            images.pop(idx)

        remaining = tuple(images)
        selected_index = state.selected_index
        next_selected: int | None = None

        if remaining:
            if selected_index is not None and 0 <= selected_index < len(state.images):
                selected_path = state.images[selected_index].path
                if selected_path not in removed_paths:
                    next_selected = next(
                        (idx for idx, item in enumerate(remaining) if item.path == selected_path),
                        None,
                    )

            if next_selected is None:
                for candidate_idx in range(0, len(state.images)):
                    candidate_path = state.images[candidate_idx].path
                    if candidate_path not in removed_paths:
                        next_selected = next(
                            (idx for idx, item in enumerate(remaining) if item.path == candidate_path),
                            None,
                        )
                        if next_selected is not None:
                            break

            if next_selected is None:
                next_selected = 0
        else:
            next_selected = None

        return replace(
            state,
            images=remaining,
            selected_index=next_selected,
            proxy_ready=bool(remaining),
            status_message=(
                f"Removed {len(valid_rows)} frame(s)."
                if remaining
                else "Import eclipse photos to begin, or drop files here."
            ),
            error_message=None,
        )
