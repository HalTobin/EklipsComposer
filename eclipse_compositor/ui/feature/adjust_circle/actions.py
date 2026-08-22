"""Actions for the adjust circle feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eclipse_compositor.cv.detection import DiscDetection


class AdjustCircleAction:
    """Base class for adjust-circle actions."""


@dataclass(frozen=True)
class OpenAdjustCircle(AdjustCircleAction):
    index: int
    path: Path
    threshold: int


@dataclass(frozen=True)
class UpdateAdjustCircleThreshold(AdjustCircleAction):
    value: int


@dataclass(frozen=True)
class AutoDetect(AdjustCircleAction):
    pass


@dataclass(frozen=True)
class ToggleCircleVisibility(AdjustCircleAction):
    visible: bool


@dataclass(frozen=True)
class LoadAdjustCircleImageResult(AdjustCircleAction):
    image: object  # np.ndarray
    detection: DiscDetection | None


@dataclass(frozen=True)
class DetectCircleResult(AdjustCircleAction):
    detection: DiscDetection | None


@dataclass(frozen=True)
class AdjustCircleFailed(AdjustCircleAction):
    message: str


@dataclass(frozen=True)
class ApplyAdjustment(AdjustCircleAction):
    pass
