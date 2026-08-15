"""Use case for clearing the gallery and preview state."""

from __future__ import annotations

from dataclasses import dataclass, replace

from eclipse_compositor.ui.state import DEFAULT_MAX_RESOLUTION, JobStatus, ScreenState


@dataclass(frozen=True)
class ClearImagesUseCase:
    """Reset the gallery to the initial empty state."""

    def invoke(self, state: ScreenState) -> ScreenState:
        return replace(
            state,
            images=(),
            preview_bgr=None,
            selected_preview_bgr=None,
            selected_index=None,
            proxy_ready=False,
            native_max_resolution=DEFAULT_MAX_RESOLUTION,
            last_project_path=None,
            import_status=JobStatus.IDLE,
            export_status=JobStatus.IDLE,
            preview_status=JobStatus.IDLE,
            status_message="Import eclipse photos to begin, or drop files here.",
            error_message=None,
        )
