"""Use case for requesting a preview render."""

from __future__ import annotations

from dataclasses import dataclass

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class RequestPreviewUseCase:
    """Signal that the preview should be refreshed if the screen is ready."""

    def invoke(self, state: ScreenState) -> ScreenState:
        return state
