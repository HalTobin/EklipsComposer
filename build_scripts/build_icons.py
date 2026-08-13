#!/usr/bin/env python3
"""Build ``assets/app_icon_darwin.icns`` from the Icon Composer 1024 PNG.

The iOS 1024 export fills the canvas. macOS Dock icons need inset artwork
or they read larger than other apps. This scales the master to 80% and
centers it on a transparent 1024 canvas before ``iconutil``.

    python build_scripts/build_icons.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DARWIN_PNG = ROOT / "assets" / "app_icon_darwin-iOS-Default-1024x1024@1x.png"
ICNS_PATH = ROOT / "assets" / "app_icon_darwin.icns"

# iOS 1024 is full-bleed; ~80% matches typical macOS Dock scale.
_MACOS_ICON_SCALE = 0.80
_CANVAS = 1024

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
    inner = max(1, int(round(_CANVAS * _MACOS_ICON_SCALE)))
    art = src.resize((inner, inner), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (_CANVAS, _CANVAS), (0, 0, 0, 0))
    origin = (_CANVAS - inner) // 2
    canvas.paste(art, (origin, origin), art)
    return canvas


def build_icns(master: Path = DARWIN_PNG, dest: Path = ICNS_PATH) -> Path:
    """Write a multi-resolution ``.icns`` from the 1024×1024 Darwin PNG."""
    if sys.platform != "darwin":
        raise RuntimeError("iconutil is only available on macOS")
    if not master.is_file():
        raise FileNotFoundError(f"Missing Darwin icon master: {master}")

    padded = _padded_master(master)
    with tempfile.TemporaryDirectory(prefix="vultureklips-iconset-") as tmp:
        iconset = Path(tmp) / "app_icon.iconset"
        iconset.mkdir()
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
    return dest


def main() -> int:
    """Build ``assets/app_icon_darwin.icns`` from the Icon Composer PNG."""
    path = build_icns()
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
