"""State for the adjust circle feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from eclipse_compositor.cv.detection import DiscDetection


@dataclass(frozen=True)
class AdjustCircleState:
    """Screen state for the adjust circle modal."""

    image_index: int | None = None
    path: Path | None = None
    threshold: int = 180
    show_circle: bool = True
    image_bgr: np.ndarray | None = None
    detection: DiscDetection | None = None
    # Manual override fields
    manual_center: tuple[int, int] | None = None
    manual_radius: float | None = None
    error_message: str | None = None
    is_loading: bool = False
    is_ready: bool = False
