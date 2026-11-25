#!/usr/bin/env bash
# Launch EVENTRA through the self-contained macOS app bundle.
# This keeps macOS camera permission attributed to EVENTRA, not bare Python.
set -e

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_BUNDLE="$SOURCE_DIR/dist/EVENTRA.app"
DATA_DIR="${EVENTRA_DATA_DIR:-$HOME/Library/Application Support/EVENTRA/data}"
PYTHON_BIN="/opt/homebrew/bin/python3.12"
TCL_INIT="/opt/homebrew/opt/tcl-tk/lib/tcl9.1/init.tcl"

# The bundled Python links against Homebrew's Tcl/Tk 9.1. If that formula was
# removed by a brew cleanup, the app crashes on startup with a missing
# init.tcl error, so restore it before launching.
if [ ! -f "$TCL_INIT" ] && command -v brew >/dev/null 2>&1; then
  echo "Tcl/Tk runtime missing. Installing python@3.12 and python-tk@3.12..."
  brew install python@3.12 python-tk@3.12
fi

if [ ! -d "$APP_BUNDLE" ]; then
  echo "EVENTRA app bundle not found. Building it..."
  if [ ! -x "$PYTHON_BIN" ]; then
    echo "Python 3.12 not found at $PYTHON_BIN."
    echo "Install it with: brew install python@3.12 python-tk@3.12"
    exit 1
  fi
  if [ ! -x "$SOURCE_DIR/.venv/bin/python" ]; then
    "$PYTHON_BIN" -m venv "$SOURCE_DIR/.venv"
    "$SOURCE_DIR/.venv/bin/python" -m pip install --upgrade pip
    "$SOURCE_DIR/.venv/bin/python" -m pip install -r "$SOURCE_DIR/requirements.txt"
  fi
  (cd "$SOURCE_DIR" && .venv/bin/python setup.py py2app)
fi

mkdir -p "$DATA_DIR"

if [ ! -f "$DATA_DIR/eventra.db" ] && [ -f "$SOURCE_DIR/data/eventra.db" ]; then
  echo "Copying EVENTRA data to $DATA_DIR..."
  cp -R "$SOURCE_DIR/data/." "$DATA_DIR/"
fi

export EVENTRA_DATA_DIR="$DATA_DIR"
open "$APP_BUNDLE" --args "$@"
