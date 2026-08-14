"""Repository contract for persisting ``ProjectBlueprint`` archives."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from eclipse_compositor.project.domain.models import LoadedProject, ProjectBlueprint

ProgressCallback = Callable[[float, str], None]


class ProjectRepository(Protocol):
    """Read and write VulturEklips project archives.

    Implementations live in the data layer. The domain never depends on zip
    or JSON details.
    """

    def save(
        self,
        blueprint: ProjectBlueprint,
        archive_path: Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        """Write *blueprint* (settings + source images) to *archive_path*."""

    def load(self, archive_path: Path, extract_dir: Path) -> LoadedProject:
        """Extract *archive_path* into *extract_dir* and return the document."""
