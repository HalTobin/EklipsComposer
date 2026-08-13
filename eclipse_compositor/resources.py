"""Resolve static asset paths for source checkouts and frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


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


def app_icon_path() -> Path:
    """Return the native app-icon file for the current platform.

    Frozen macOS builds use the ``.icns`` PyInstaller already copies into
    ``Contents/Resources`` (not a second copy under ``assets/``).
    """
    name = _icon_filename()
    assets = assets_dir()
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", "."))
        candidates.extend(
            (
                meipass / name,
                meipass / "assets" / name,
                meipass.parent / "Resources" / name,
                meipass.parent / "Resources" / "assets" / name,
            )
        )
    candidates.extend(
        (
            assets / name,
            assets / "app_icon_darwin-iOS-Default-1024x1024@1x.png",
            assets / "app_icon_linux.png",
            assets / "app_icon.svg",
        )
    )
    for path in candidates:
        if path.is_file():
            return path
    return assets / "app_icon.svg"
