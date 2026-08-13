#!/bin/sh
# Build the macOS .app into repo/output/VulturEklips.app
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
# Drop the full Qt Addons / GUI OpenCV wheels if a previous env pulled them in.
"$PYTHON" -m pip uninstall -y PySide6 PySide6-Addons opencv-python opencv-python-headless || true
"$PYTHON" -m pip install -r "$ROOT/requirements-build.txt"

echo "Building macOS icon…"
"$PYTHON" "$ROOT/build_scripts/build_icons.py"

echo "Packaging VulturEklips.app…"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --distpath "$ROOT/output" \
  --workpath "$ROOT/output/work" \
  "$ROOT/vultureklips.spec"

# Leave only the runnable bundle in output/.
rm -rf "$ROOT/output/work" "$ROOT/output/VulturEklips"

APP="$ROOT/output/VulturEklips.app"
if [ ! -d "$APP" ]; then
  echo "Build finished but $APP was not created." >&2
  exit 1
fi

echo "Built $APP"
