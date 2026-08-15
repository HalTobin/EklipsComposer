"""Immutable UI state for the main compositor screen (MVI)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from eclipse_compositor.cv.layout import LayoutDirection, LayoutType

# Floor for the resolution slider when no images are loaded yet.
DEFAULT_MAX_RESOLUTION: int = 2400
MIN_RESOLUTION: int = 200

# Colorimetry identity (Reset restores these).
DEFAULT_CONTRAST: float = 1.0
DEFAULT_SATURATION: float = 1.0
DEFAULT_BRIGHTNESS: float = 0.0
DEFAULT_GAMMA: float = 1.0
DEFAULT_TEMPERATURE: float = 0.0

# Circular mask defaults (mask is off until the user enables it).
DEFAULT_MASK_SIZE: float = 0.90
DEFAULT_MASK_FEATHER: float = 0.20

# Canvas margin around the laid-out frames (px per side). Negative crops in.
DEFAULT_MARGIN: int = 40
MIN_MARGIN: int = -4000
MAX_MARGIN: int = 4000


class SidebarTab(str, Enum):
    """Active page in the sidebar parameter tabs."""

    COMPOSITE = "composite"
    COLORIMETRY = "colorimetry"
    MASK = "mask"
    CANVAS = "canvas"


class JobStatus(str, Enum):
    """Background job lifecycle for preview / export / import."""

    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


class BlockingJob(str, Enum):
    """Long-running file job that locks the editor behind an overlay."""

    SAVE = "save"
    OPEN = "open"
    EXPORT = "export"


@dataclass(frozen=True)
class ImageItem:
    """One imported frame in the gallery."""

    path: Path
    enabled: bool = True
    detection_ok: bool | None = None  # None = not yet evaluated
    thumbnail_path: str | None = None  # small JPEG for the gallery list icon


@dataclass(frozen=True)
class ScreenState:
    """Complete snapshot of the main screen UI.

    Views render exclusively from this object; never mutate in place —
    use ``dataclasses.replace``.
    """

    images: tuple[ImageItem, ...] = ()
    crop_size: int = 800  # per-frame square resolution (px)
    spacing: float = -0.15  # negative = overlap (typical for eclipse sequences)
    layout: LayoutType = LayoutType.ARC
    arc_angle: float = 120.0  # signed sweep degrees, −180…180
    direction: LayoutDirection = LayoutDirection.HORIZONTAL
    threshold: int = 180
    grid_columns: int = 3
    grid_rows: int = 2
    # Max square crop allowed = largest native min(h, w) among imports.
    native_max_resolution: int = DEFAULT_MAX_RESOLUTION
    preview_bgr: object | None = None  # np.ndarray | None; object avoids import cycle
    selected_preview_bgr: object | None = None  # proxy of the selected gallery frame
    status_message: str = "Import eclipse photos to begin, or drop files here."
    import_status: JobStatus = JobStatus.IDLE
    preview_status: JobStatus = JobStatus.IDLE
    export_status: JobStatus = JobStatus.IDLE
    progress: float = 0.0  # 0–1
    last_export_path: Path | None = None
    last_project_path: Path | None = None
    dirty: bool = False  # unsaved project, or edits since last open/save
    blocking_job: BlockingJob | None = None
    blocking_job_path: Path | None = None
    blocking_job_cancelling: bool = False
    error_message: str | None = None
    selected_index: int | None = None
    proxy_ready: bool = False
    zoom: float = 1.0
    sidebar_tab: SidebarTab = SidebarTab.COMPOSITE
    contrast: float = DEFAULT_CONTRAST
    saturation: float = DEFAULT_SATURATION
    brightness: float = DEFAULT_BRIGHTNESS
    gamma: float = DEFAULT_GAMMA
    temperature: float = DEFAULT_TEMPERATURE
    mask_enabled: bool = False
    mask_size: float = DEFAULT_MASK_SIZE
    mask_feather: float = DEFAULT_MASK_FEATHER
    margin_linked: bool = True
    margin_x: int = DEFAULT_MARGIN
    margin_y: int = DEFAULT_MARGIN

    # Internal bookkeeping (not rendered directly)
    _proxy_generation: int = 0
    _preview_generation: int = 0


def enabled_paths(state: ScreenState) -> list[Path]:
    """Return enabled frame paths in gallery order."""
    return [item.path for item in state.images if item.enabled]


def default_state() -> ScreenState:
    """Factory for the initial empty screen state."""
    return ScreenState()


def native_max_from_shapes(shapes: dict[Path, tuple[int, int]]) -> int:
    """Largest square that fits in any imported image (max of min sides)."""
    if not shapes:
        return DEFAULT_MAX_RESOLUTION
    return max(MIN_RESOLUTION, max(min(h, w) for h, w in shapes.values()))
