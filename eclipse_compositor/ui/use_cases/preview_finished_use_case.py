"""Use case for applying the results of a completed preview render."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class PreviewFinishedUseCase:
    """Store a rendered preview and attach the detection metadata."""

    def invoke(
        self,
        state: ScreenState,
        preview_bgr: object,
        generation: int,
        skipped: tuple = (),
        detection_flags: tuple = (),
    ) -> ScreenState:
        flag_map = dict(detection_flags)
        updated = tuple(
            replace(item, detection_ok=flag_map.get(item.path))
            for item in state.images
        )
        skip_note = f" Skipped {len(skipped)} (no disc)." if skipped else ""
        return replace(
            state,
            images=updated,
            preview_bgr=preview_bgr,
            progress=1.0,
            status_message=f"Preview updated.{skip_note}",
            error_message=None,
            _preview_generation=generation,
            preview_status=None,
        )
