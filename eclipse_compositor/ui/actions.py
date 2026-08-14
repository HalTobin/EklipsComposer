"""UI intents / actions for the main compositor screen (MVI)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.ui.state import ImageItem


class ScreenAction:
    """Base class for all UI events dispatched to the ViewModel."""


@dataclass(frozen=True)
class LoadImages(ScreenAction):
    """User selected files or a folder to import."""

    paths: tuple[Path, ...]
    video_frame_step: int = 1


@dataclass(frozen=True)
class ClearImages(ScreenAction):
    """Remove all imported frames."""


@dataclass(frozen=True)
class ToggleImage(ScreenAction):
    """Enable or disable a gallery frame by index."""

    index: int
    enabled: bool


@dataclass(frozen=True)
class SelectImage(ScreenAction):
    """Highlight a gallery item."""

    index: int | None


@dataclass(frozen=True)
class ReorderImages(ScreenAction):
    """Replace the image list order (after drag-sort or chronological re-sort)."""

    images: tuple[ImageItem, ...]


@dataclass(frozen=True)
class UpdateCropSize(ScreenAction):
    value: int


@dataclass(frozen=True)
class UpdateSpacing(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateLayout(ScreenAction):
    value: LayoutType


@dataclass(frozen=True)
class UpdateArcAngle(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateDirection(ScreenAction):
    value: LayoutDirection


@dataclass(frozen=True)
class UpdateThreshold(ScreenAction):
    value: int


@dataclass(frozen=True)
class UpdateGridColumns(ScreenAction):
    value: int


@dataclass(frozen=True)
class UpdateGridRows(ScreenAction):
    value: int


@dataclass(frozen=True)
class UpdateZoom(ScreenAction):
    value: float


@dataclass(frozen=True)
class RequestPreview(ScreenAction):
    """Ask the ViewModel to (re)render the proxy composite."""


@dataclass(frozen=True)
class ExportComposite(ScreenAction):
    """Kick off a full-resolution export."""

    output_path: Path


# --- Worker → ViewModel result actions ---


@dataclass(frozen=True)
class ImportProgress(ScreenAction):
    progress: float
    message: str


@dataclass(frozen=True)
class ImportFinished(ScreenAction):
    images: tuple[ImageItem, ...]
    generation: int


@dataclass(frozen=True)
class ImportFailed(ScreenAction):
    message: str


@dataclass(frozen=True)
class PreviewProgress(ScreenAction):
    progress: float
    message: str


@dataclass(frozen=True)
class PreviewFinished(ScreenAction):
    preview_bgr: object  # np.ndarray
    generation: int
    skipped: tuple[Path, ...]
    detection_flags: tuple[tuple[Path, bool], ...]


@dataclass(frozen=True)
class PreviewFailed(ScreenAction):
    message: str
    generation: int


@dataclass(frozen=True)
class ExportProgress(ScreenAction):
    progress: float
    message: str


@dataclass(frozen=True)
class ExportFinished(ScreenAction):
    output_path: Path
    skipped: tuple[Path, ...]


@dataclass(frozen=True)
class ExportFailed(ScreenAction):
    message: str
