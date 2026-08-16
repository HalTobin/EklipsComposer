"""Domain models for the Licenses feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class License:
    """A single license text attached to a dependency."""

    name: str
    text: str


@dataclass(frozen=True)
class Dependency:
    """A third-party project bundled with or used by the app."""

    name: str
    developer: str
    repository_url: str
    licenses: tuple[License, ...]
