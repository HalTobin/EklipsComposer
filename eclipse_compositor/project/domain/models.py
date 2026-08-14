"""Persistable composition snapshot — independent of UI and I/O format."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FORMAT_ID: str = "vultureklips"
FORMAT_VERSION: int = 1
PROJECT_SUFFIX: str = ".vlt"
COMPOSITION_FILENAME: str = "composition.json"
RESOURCE_DIR: str = "res"

ALLOWED_LAYOUTS: frozenset[str] = frozenset({"linear", "arc", "grid"})
ALLOWED_DIRECTIONS: frozenset[str] = frozenset(
    {"horizontal", "diagonal", "vertical", "diagonal_reverse"}
)


def is_project_file(path: Path | str) -> bool:
    """Return True if *path* has the VulturEklips project suffix."""
    return Path(path).suffix.lower() == PROJECT_SUFFIX


@dataclass(frozen=True)
class CompositeSettings:
    """Layout and detection parameters for the composite."""

    crop_size: int
    spacing: float
    layout: str
    arc_angle: float
    direction: str
    threshold: int
    grid_columns: int
    grid_rows: int


@dataclass(frozen=True)
class ColorimetrySettings:
    """Color grade applied to the finished composite."""

    contrast: float
    saturation: float
    brightness: float
    gamma: float
    temperature: float


@dataclass(frozen=True)
class MaskSettings:
    """Per-frame circular fade-to-black mask."""

    enabled: bool
    size: float
    feather: float


@dataclass(frozen=True)
class FrameSource:
    """A gallery frame on disk, ready to pack into an archive."""

    source_path: Path
    enabled: bool


@dataclass(frozen=True)
class FrameRecord:
    """A packed frame inside a project archive."""

    file: str
    enabled: bool


@dataclass(frozen=True)
class ProjectBlueprint:
    """In-memory project to persist: settings plus original frame files."""

    composite: CompositeSettings
    colorimetry: ColorimetrySettings
    mask: MaskSettings
    frames: tuple[FrameSource, ...]


@dataclass(frozen=True)
class ProjectDocument:
    """Fully specified project as stored in ``composition.json``."""

    version: int
    composite: CompositeSettings
    colorimetry: ColorimetrySettings
    mask: MaskSettings
    frames: tuple[FrameRecord, ...]


@dataclass(frozen=True)
class LoadedProject:
    """Document plus extracted frame paths in gallery order."""

    document: ProjectDocument
    frame_paths: tuple[Path, ...]
    extract_root: Path
