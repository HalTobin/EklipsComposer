"""Use case for applying the results of a completed import."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class ImportFinishedUseCase:
    """Apply imported gallery results while keeping a valid selected index."""

    def invoke(
        self,
        state: ScreenState,
        images: tuple,
        generation: int,
        native_max_resolution: int,
    ) -> ScreenState:
        existing = list(state.images)
        existing_paths = {item.path for item in existing}
        merged = existing + [img for img in images if img.path not in existing_paths]
        merged_tuple = tuple(merged)

        selected = state.selected_index
        if selected is None and merged_tuple:
            selected = 0
        elif selected is not None and selected >= len(merged_tuple):
            selected = 0 if merged_tuple else None

        return replace(
            state,
            images=merged_tuple,
            selected_index=selected,
            native_max_resolution=native_max_resolution,
            crop_size=min(state.crop_size, native_max_resolution),
            proxy_ready=True,
            import_status=None,
            progress=1.0,
            status_message=(
                f"Imported {len(images)} frame(s). "
                "Preview updates live as you adjust settings."
            ),
            error_message=None,
            _proxy_generation=generation,
        )
