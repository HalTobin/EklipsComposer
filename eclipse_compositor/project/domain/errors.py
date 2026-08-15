"""Domain errors for project save and open."""


class ProjectError(Exception):
    """Base error for project persistence failures."""


class ProjectFormatError(ProjectError):
    """The archive is not a valid EklipsComposer project."""


class ProjectIoError(ProjectError):
    """Filesystem or archive I/O failed while saving or opening."""
