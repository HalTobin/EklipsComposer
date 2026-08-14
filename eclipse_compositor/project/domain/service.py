"""Application service for saving and opening composition projects."""

from __future__ import annotations

from pathlib import Path

from eclipse_compositor.project.domain.errors import ProjectError
from eclipse_compositor.project.domain.models import (
    PROJECT_SUFFIX,
    LoadedProject,
    ProjectBlueprint,
)
from eclipse_compositor.project.domain.repository import ProgressCallback, ProjectRepository


class ProjectService:
    """Domain use-cases: validate, then delegate persistence to a repository."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def save(
        self,
        blueprint: ProjectBlueprint,
        archive_path: Path,
        progress: ProgressCallback | None = None,
    ) -> Path:
        """Persist *blueprint* to a ``.vlt`` archive.

        Args:
            blueprint: Settings plus source frame paths in gallery order.
            archive_path: Destination path (``.vlt`` is appended if missing).
            progress: Optional ``(fraction, message)`` callback.

        Returns:
            The path actually written.

        Raises:
            ProjectError: If there are no frames or the repository fails.
        """
        if not blueprint.frames:
            raise ProjectError("A project must contain at least one frame.")
        dest = Path(archive_path)
        if dest.suffix.lower() != PROJECT_SUFFIX:
            dest = dest.with_suffix(PROJECT_SUFFIX)
        self._repository.save(blueprint, dest, progress=progress)
        return dest

    def open(self, archive_path: Path, extract_dir: Path) -> LoadedProject:
        """Load a ``.vlt`` archive into *extract_dir*.

        Args:
            archive_path: Project file to open.
            extract_dir: Directory that will hold ``composition.json`` and ``res/``.

        Returns:
            Document and extracted frame paths in saved order.
        """
        path = Path(archive_path)
        if not path.is_file():
            raise ProjectError(f"Project file not found: {path}")
        return self._repository.load(path, Path(extract_dir))
