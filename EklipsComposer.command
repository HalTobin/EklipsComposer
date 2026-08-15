#!/bin/zsh
# Double-click this file in Finder to launch EklipsComposer.
set -euo pipefail

cd "$(dirname "$0")"

if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python main.py
elif [[ -x venv/bin/python ]]; then
  exec venv/bin/python main.py
else
  exec python3 main.py
fi
