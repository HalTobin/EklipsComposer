#!/usr/bin/env python3
"""Build macOS Dock assets from the Icon Composer 1024 PNG.

The iOS 1024 export is a full-bleed squircle. macOS Dock / Finder icons
follow Apple's 1024pt grid, where the squircle is 824pt — otherwise the
icon reads larger than every other app. This scales the master to 824 and
centers it on a transparent 1024 canvas, then writes:

* ``assets/app_icon_darwin.png`` — used by source checkouts via QIcon
* ``assets/app_icon_darwin.icns`` — used by the packaged ``.app`` (macOS)

    python build_scripts/build_icons.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DARWIN_PNG = ROOT / "assets" / "app_icon_darwin-iOS-Default-1024x1024@1x.png"
PADDED_PNG = ROOT / "assets" / "app_icon_darwin.png"
ICNS_PATH = ROOT / "assets" / "app_icon_darwin.icns"

# Apple macOS icon grid: 824pt squircle on a 1024pt canvas.
_CANVAS = 1024
_MACOS_ICON_SIDE = 824

# iconutil expects this exact filename set (1x + @2x for each point size).
_ICONSET_SPECS: tuple[tuple[str, int], ...] = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)


def _padded_master(master: Path) -> Image.Image:
    """Scale the iOS 1024 art down and center it on a transparent canvas."""
    src = Image.open(master).convert("RGBA")
    art = src.resize((_MACOS_ICON_SIDE, _MACOS_ICON_SIDE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (_CANVAS, _CANVAS), (0, 0, 0, 0))
    origin = (_CANVAS - _MACOS_ICON_SIDE) // 2
    canvas.paste(art, (origin, origin), art)
    return canvas


def build_padded_png(master: Path = DARWIN_PNG, dest: Path = PADDED_PNG) -> Path:
    """Write the Dock-sized 1024 PNG used by source checkouts."""
    if not master.is_file():
        raise FileNotFoundError(f"Missing Darwin icon master: {master}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    _padded_master(master).save(dest, "PNG")
    return dest


def build_icns(master: Path = DARWIN_PNG, dest: Path = ICNS_PATH) -> Path:
    """Write a multi-resolution ``.icns`` from the 1024×1024 Darwin PNG."""
    if sys.platform != "darwin":
        raise RuntimeError("iconutil is only available on macOS")
    if not master.is_file():
        raise FileNotFoundError(f"Missing Darwin icon master: {master}")

    padded = _padded_master(master)
    iconset = dest.parent / "app_icon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    try:
        master_png = iconset / "icon_512x512@2x.png"
        padded.save(master_png, "PNG")
        for name, px in _ICONSET_SPECS:
            out = iconset / name
            if px == 1024:
                continue
            subprocess.run(
                ["sips", "-z", str(px), str(px), str(master_png), "--out", str(out)],
                check=True,
                capture_output=True,
            )
        subprocess.run(
            ["iconutil", "-c", "icns", "-o", str(dest), str(iconset)],
            check=True,
        )
    finally:
        shutil.rmtree(iconset, ignore_errors=True)
    return dest


def main() -> int:
    """Build the padded macOS PNG and, on Darwin, the ``.icns``."""
    png = build_padded_png()
    print(f"Wrote {png} ({png.stat().st_size} bytes)")
    if sys.platform == "darwin":
        path = build_icns()
        print(f"Wrote {path} ({path.stat().st_size} bytes)")
    else:
        print("Skipping .icns (iconutil is macOS-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
