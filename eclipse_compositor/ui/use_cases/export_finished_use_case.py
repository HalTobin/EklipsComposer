"""Use case for applying the result of a completed export job."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class ExportFinishedUseCase:
    """Finalize the export state and record the output path."""

    def invoke(
        self,
        state: ScreenState,
        output_path: Path,
        skipped: tuple = (),
    ) -> ScreenState:
        skip_note = f" Skipped {len(skipped)} frame(s)." if skipped else ""
        return replace(
            state,
            last_export_path=output_path,
            export_status=None,
            progress=1.0,
            status_message=f"Exported to {output_path}.{skip_note}",
            error_message=None,
        )
