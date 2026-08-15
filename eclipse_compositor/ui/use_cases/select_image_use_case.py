"""Use case for selecting the highlighted gallery item."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from eclipse_compositor.ui.state import ScreenState


@dataclass(frozen=True)
class SelectImageUseCase:
    """Attach the selected preview for the chosen gallery frame."""

    def invoke(
        self,
        state: ScreenState,
        index: int | None,
        proxy_cache: Mapping[Path, np.ndarray] | None = None,
    ) -> ScreenState:
        images = state.images
        if index is not None and not (0 <= index < len(images)):
            index = None

        preview = None
        if index is not None and proxy_cache is not None:
            preview = proxy_cache.get(images[index].path)

        return replace(
            state,
            selected_index=index,
            selected_preview_bgr=preview,
        )
