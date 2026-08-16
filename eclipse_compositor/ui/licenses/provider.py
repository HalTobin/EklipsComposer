"""Dependency data source abstraction.

``DependencyProvider`` is the seam for fetching the bundled/third-party
dependency catalog. ``StaticDependencyProvider`` returns the catalog known at
build time; a future provider can fetch this dynamically (for example from
package metadata or a remote manifest) without touching the use cases,
view model, or view.
"""

from __future__ import annotations

from typing import Protocol

from eclipse_compositor.ui.licenses import license_texts as texts
from eclipse_compositor.ui.licenses.models import Dependency, License


class DependencyProvider(Protocol):
    """Supplies the list of dependencies to display."""

    def fetch(self) -> tuple[Dependency, ...]:
        """Return the current dependency catalog."""
        ...


class StaticDependencyProvider:
    """Hardcoded fallback catalog, used until dynamic fetching is wired up."""

    def fetch(self) -> tuple[Dependency, ...]:
        lgpl = License("GNU Lesser General Public License v3.0", texts.LGPL_V3)
        mit = License("MIT License", texts.MIT_LICENSE)
        bsd = License("BSD 3-Clause License", texts.BSD_3_CLAUSE)
        ffmpeg_licenses = (
            License("GNU Lesser General Public License v2.1+ / GPL v2+", texts.LGPL_V3),
            License("FFmpeg licensing notice", texts.FFMPEG_NOTICE),
        )
        return (
            Dependency(
                name="EklipsComposer",
                developer="Alexis ANEAS",
                repository_url="https://github.com/HalTobin/EklipsComposer",
                licenses=(mit,),
            ),
            Dependency(
                name="PySide6",
                developer="The Qt Company",
                repository_url="https://github.com/pyside/pyside-setup",
                licenses=(lgpl,),
            ),
            Dependency(
                name="Qt",
                developer="The Qt Company",
                repository_url="https://github.com/qt/qtbase",
                licenses=(lgpl,),
            ),
            Dependency(
                name="NumPy",
                developer="NumPy Developers",
                repository_url="https://github.com/numpy/numpy",
                licenses=(bsd,),
            ),
            Dependency(
                name="Pillow",
                developer="Pillow contributors",
                repository_url="https://github.com/python-pillow/Pillow",
                licenses=(mit,),
            ),
            Dependency(
                name="piexif",
                developer="hMatoba",
                repository_url="https://github.com/hMatoba/piexif",
                licenses=(mit,),
            ),
            Dependency(
                name="FFmpeg",
                developer="FFmpeg team",
                repository_url="https://github.com/FFmpeg/FFmpeg",
                licenses=ffmpeg_licenses,
            ),
        )
