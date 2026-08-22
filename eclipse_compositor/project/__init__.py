"""Project persistence: save and open EklipsComposer ``.vlt`` archives."""

from eclipse_compositor.project.data.zip_store import ZipProjectRepository
from eclipse_compositor.project.domain.errors import (
    ProjectError,
    ProjectFormatError,
    ProjectIoError,
)
from eclipse_compositor.project.domain.models import (
    FORMAT_VERSION,
    PROJECT_SUFFIX,
    ColorimetrySettings,
    CompositeSettings,
    FrameSource,
    LoadedProject,
    MaskSettings,
    ManualDetection,
    ProjectBlueprint,
    ProjectDocument,
    is_project_file,
)
from eclipse_compositor.project.domain.service import ProjectService


def default_project_service() -> ProjectService:
    """Return a ``ProjectService`` backed by the zip ``.vlt`` store."""
    return ProjectService(ZipProjectRepository())


__all__ = [
    "FORMAT_VERSION",
    "PROJECT_SUFFIX",
    "ColorimetrySettings",
    "CompositeSettings",
    "FrameSource",
    "LoadedProject",
    "MaskSettings",
    "ProjectBlueprint",
    "ProjectDocument",
    "ProjectError",
    "ProjectFormatError",
    "ProjectIoError",
    "ProjectService",
    "ZipProjectRepository",
    "default_project_service",
    "is_project_file",
]
