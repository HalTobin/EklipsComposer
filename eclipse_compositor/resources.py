"""Resolve static asset paths for source checkouts and frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path

_MARK_FILENAMES: tuple[str, ...] = (
    "app_icon_darwin-iOS-Default-1024x1024@1x.png",
    "app_icon.png",
    "app_icon_linux.png",
    "app_icon.svg",
)


def project_root() -> Path:
    """Return the repo root, or PyInstaller's bundle dir when frozen.

    PyInstaller extracts/collects data files under ``sys._MEIPASS``. In a
    normal checkout this is the directory that contains ``assets/``.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def assets_dir() -> Path:
    """Return the directory that holds app icons and other static files."""
    return project_root() / "assets"


def _icon_filename() -> str:
    """Return the platform-native icon filename."""
    if sys.platform == "darwin":
        return "app_icon_darwin.icns"
    if sys.platform == "win32":
        return "app_icon_win.ico"
    return "app_icon_linux.png"


def _search_roots() -> list[Path]:
    """Return directories that may hold bundled icons.

    Frozen macOS apps put ``datas`` under ``Contents/Resources``, while
    ``sys._MEIPASS`` is typically ``Contents/MacOS`` or ``Contents/Frameworks``.
    """
    roots: list[Path] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        key = str(path)
        if key in seen:
            return
        seen.add(key)
        roots.append(path)

    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", "."))
        _add(meipass)
        _add(meipass / "assets")
        _add(meipass.parent / "Resources")
        _add(meipass.parent / "Resources" / "assets")
    _add(assets_dir())
    return roots


def _first_file(*names: str) -> Path | None:
    """Return the first existing file named in *names* under search roots.

    Names are the priority order: a PNG in a later root beats an ``.icns``
    sitting in ``Contents/Resources``.
    """
    roots = _search_roots()
    for name in names:
        for root in roots:
            path = root / name
            if path.is_file():
                return path
    return None


def app_icon_path() -> Path:
    """Return the native window / Dock icon for the current platform.

    QIcon cannot decode ``.icns`` / ``.ico`` in the packaged app (those Qt
    plugins are stripped). Prefer a PNG, and keep the bundle ``.icns`` for
    Finder / Launchpad via ``CFBundleIconFile``.
    """
    png_names: tuple[str, ...] = ()
    if sys.platform == "darwin":
        png_names = (
            "app_icon_darwin.png",
            "app_icon_darwin-iOS-Default-1024x1024@1x.png",
        )
    found = _first_file(*png_names, _icon_filename(), *_MARK_FILENAMES)
    if found is not None:
        return found
    return assets_dir() / "app_icon.svg"


def app_mark_path() -> Path:
    """Return the full-bleed mark for in-app chrome (sidebar, about).

    Unlike :func:`app_icon_path`, this prefers the Icon Composer iOS
    export so the squircle fills a fixed-size ``QLabel`` instead of
    inheriting Dock padding.
    """
    found = _first_file(*_MARK_FILENAMES)
    if found is not None:
        return found
    return app_icon_path()
