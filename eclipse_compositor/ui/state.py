"""Immutable UI state for the main compositor screen (MVI)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from eclipse_compositor.cv.layout import LayoutType

# Floor for the resolution slider when no images are loaded yet.
DEFAULT_MAX_RESOLUTION: int = 2400
MIN_RESOLUTION: int = 200


class JobStatus(str, Enum):
    """Background job lifecycle for preview / export / import."""

    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


@dataclass(frozen=True)
class ImageItem:
    """One imported frame in the gallery."""

    path: Path
    enabled: bool = True
    detection_ok: bool | None = None  # None = not yet evaluated
    thumbnail_path: str | None = None


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
    curvature: float = 0.35
    threshold: int = 180
    grid_columns: int = 3
    grid_rows: int = 2
    # Max square crop allowed = largest native min(h, w) among imports.
    native_max_resolution: int = DEFAULT_MAX_RESOLUTION
    preview_bgr: object | None = None  # np.ndarray | None; object avoids import cycle
    status_message: str = "Import eclipse photos to begin."
    import_status: JobStatus = JobStatus.IDLE
    preview_status: JobStatus = JobStatus.IDLE
    export_status: JobStatus = JobStatus.IDLE
    progress: float = 0.0  # 0–1
    last_export_path: Path | None = None
    error_message: str | None = None
    selected_index: int | None = None
    proxy_ready: bool = False
    zoom: float = 1.0

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
