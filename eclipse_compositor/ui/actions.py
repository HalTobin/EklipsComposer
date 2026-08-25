"""UI intents / actions for the main compositor screen (MVI)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType
from eclipse_compositor.ui.state import GallerySortMode, GalleryViewMode, ImageItem, CanvasItem, MediaItem, ProjectSortMode


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
class RemoveImage(ScreenAction):
    """Remove one or more gallery frames by index."""

    indices: tuple[int, ...]


@dataclass(frozen=True)
class SelectImage(ScreenAction):
    """Highlight a gallery item."""

    index: int | None


@dataclass(frozen=True)
class ReorderImages(ScreenAction):
    """Replace the image list order (after drag-sort or chronological re-sort)."""

    images: tuple[ImageItem, ...]


@dataclass(frozen=True)
class ToggleFavorite(ScreenAction):
    """Mark or unmark a gallery frame as favorite by index."""

    index: int
    favorite: bool


@dataclass(frozen=True)
class SetAllEnabled(ScreenAction):
    """Check or uncheck every gallery frame's enable checkbox."""

    enabled: bool


@dataclass(frozen=True)
class UpdateGalleryViewMode(ScreenAction):
    """Switch between list-with-preview, simple list, and icon views."""

    value: GalleryViewMode


@dataclass(frozen=True)
class UpdateCanvasGalleryViewMode(ScreenAction):
    """Switch the visual density of the canvas frame list."""

    value: GalleryViewMode


@dataclass(frozen=True)
class UpdateGallerySortMode(ScreenAction):
    """Sort frames by title or EXIF capture date."""

    value: GallerySortMode


@dataclass(frozen=True)
class UpdateGalleryShowOnlyFavorites(ScreenAction):
    """Filter the gallery to favorites and currently selected frame(s)."""

    value: bool


@dataclass(frozen=True)
class ToggleFavoriteAction(ScreenAction):
    """Toggle favorite state for a project media item by filepath."""

    filepath: str
    favorite: bool


@dataclass(frozen=True)
class SortProjectMediaAction(ScreenAction):
    """Change the project media sorting mode."""

    sort_mode: str


@dataclass(frozen=True)
class AddMediaToCanvasAction(ScreenAction):
    """Add a project media item to the active canvas."""

    filepath: str


@dataclass(frozen=True)
class RemoveMediaFromCanvasAction(ScreenAction):
    """Remove one active canvas item by ID."""

    canvas_item_id: str


@dataclass(frozen=True)
class ReorderCanvasMediaAction(ScreenAction):
    """Reorder the canvas media list."""

    from_index: int
    to_index: int


@dataclass(frozen=True)
class ApplyImageDetectionOverride(ScreenAction):
    """Apply a manual detection result to a gallery frame."""

    index: int
    detection: object  # DiscDetection | None


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
class SelectSidebarTab(ScreenAction):
    value: object  # SidebarTab


@dataclass(frozen=True)
class UpdateContrast(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateSaturation(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateBrightness(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateGamma(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateTemperature(ScreenAction):
    value: float


@dataclass(frozen=True)
class ResetColorimetry(ScreenAction):
    """Restore contrast / saturation / brightness / gamma / temperature."""


@dataclass(frozen=True)
class UpdateMaskEnabled(ScreenAction):
    value: bool


@dataclass(frozen=True)
class UpdateMaskSize(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateMaskFeather(ScreenAction):
    value: float


@dataclass(frozen=True)
class UpdateMarginLinked(ScreenAction):
    value: bool


@dataclass(frozen=True)
class UpdateMarginX(ScreenAction):
    value: int


@dataclass(frozen=True)
class UpdateMarginY(ScreenAction):
    value: int


@dataclass(frozen=True)
class UpdateMarginGlobal(ScreenAction):
    """Set horizontal and vertical canvas margins to the same value."""

    value: int


@dataclass(frozen=True)
class RequestPreview(ScreenAction):
    """Ask the ViewModel to (re)render the proxy composite."""


@dataclass(frozen=True)
class ExportComposite(ScreenAction):
    """Kick off a full-resolution export."""

    output_path: Path


@dataclass(frozen=True)
class SaveProject(ScreenAction):
    """Pack the current composition into a ``.vlt`` archive."""

    output_path: Path


@dataclass(frozen=True)
class OpenProject(ScreenAction):
    """Replace the current composition with a saved ``.vlt`` project."""

    path: Path


@dataclass(frozen=True)
class CancelJob(ScreenAction):
    """Request cooperative cancel of the current save / load / export."""


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


@dataclass(frozen=True)
class SaveProjectProgress(ScreenAction):
    progress: float
    message: str


@dataclass(frozen=True)
class SaveProjectFinished(ScreenAction):
    output_path: Path


@dataclass(frozen=True)
class SaveProjectFailed(ScreenAction):
    message: str


@dataclass(frozen=True)
class OpenProjectProgress(ScreenAction):
    progress: float
    message: str


@dataclass(frozen=True)
class OpenProjectFinished(ScreenAction):
    """Worker finished extracting and caching a project."""

    result: object  # ProjectOpenResult
    generation: int


@dataclass(frozen=True)
class OpenProjectFailed(ScreenAction):
    message: str
    generation: int


@dataclass(frozen=True)
class BlockingJobCancelled(ScreenAction):
    """Worker acknowledged a cancel request."""

    token: object  # threading.Event identity for the job that stopped
