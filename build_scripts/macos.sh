#!/bin/sh
# Build the macOS .app into repo/output/EklipsComposer.app
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "macos.sh must run on macOS." >&2
  exit 1
fi

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python3"
fi

echo "Installing slim build dependencies…"
# Drop the full Qt Addons / GUI OpenCV / fat ffmpeg wheels if a previous
# env pulled them in (imageio-ffmpeg ships a ~47 MB encoder-heavy binary).
"$PYTHON" -m pip uninstall -y PySide6 PySide6-Addons opencv-python opencv-python-headless imageio-ffmpeg || true
"$PYTHON" -m pip install -r "$ROOT/requirements-build.txt"

echo "Building decode-only ffmpeg…"
chmod +x "$ROOT/build_scripts/build_ffmpeg.sh"
"$ROOT/build_scripts/build_ffmpeg.sh"

echo "Building macOS icon…"
"$PYTHON" "$ROOT/build_scripts/build_icons.py"

echo "Packaging EklipsComposer.app…"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$ROOT/output" \
  --workpath "$ROOT/output/work" \
  "$ROOT/eklipscomposer.spec"

# Leave only the runnable bundle in output/.
rm -rf "$ROOT/output/work" "$ROOT/output/EklipsComposer"

APP="$ROOT/output/EklipsComposer.app"
if [ ! -d "$APP" ]; then
  echo "Build finished but $APP was not created." >&2
  exit 1
fi

echo "Built $APP"
