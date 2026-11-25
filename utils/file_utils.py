"""Filesystem helpers."""

from __future__ import annotations

import os
import platform
import re
import subprocess
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "file"


def open_path(path: Path) -> None:
    """Reveal a file/folder using the operating system's default application."""
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        elif system == "Windows":
            os.startfile(str(path))  # noqa: S606
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError:
        pass
