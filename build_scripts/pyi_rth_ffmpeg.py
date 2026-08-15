"""PyInstaller runtime hook: point video import at the bundled ffmpeg."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _bundled_ffmpeg() -> str | None:
    """Locate the decode-only ffmpeg shipped with the frozen app."""
    roots: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
    exe_dir = Path(sys.executable).resolve().parent
    roots.append(exe_dir)
    roots.append(exe_dir.parent / "Frameworks")
    names = ("ffmpeg", "ffmpeg.exe")
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate.is_file():
                return str(candidate)
    return None


_exe = _bundled_ffmpeg()
if _exe:
    os.environ.setdefault("EKLIPSCOMPOSER_FFMPEG", _exe)
