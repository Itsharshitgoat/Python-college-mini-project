"""EVENTRA - QR-Based Event Registration & Attendance Management System."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from core.app import EventraApp

        app = EventraApp()
        app.run()
        return 0
    except ImportError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        print("Install dependencies with: pip install -r requirements.txt", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - top-level guard
        print(f"EVENTRA failed to start: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
