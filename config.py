"""Application configuration and path management for EVENTRA."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "EVENTRA"
APP_TAGLINE = "QR-Based Event Registration & Attendance Management System"
APP_VERSION = "1.0.0"

DEFAULT_WINDOW_SIZE = "1366x850"
MIN_WINDOW_SIZE = (1100, 700)
LOGIN_WINDOW_SIZE = "520x640"

QR_PAYLOAD_PREFIX = "EVENTRA:V1:"
TOKEN_BYTES = 32

EVENT_STATUSES = ("DRAFT", "OPEN", "CLOSED", "COMPLETED", "CANCELLED")
CHECKIN_STATUSES = ("DISABLED", "OPEN", "CLOSED")
REGISTRATION_STATUSES = ("ACTIVE", "CANCELLED")

ROLE_ADMIN = "ADMIN"
ROLE_REGISTRATION = "REGISTRATION_OPERATOR"
ROLE_CHECKIN = "CHECKIN_OPERATOR"
ROLES = (ROLE_ADMIN, ROLE_REGISTRATION, ROLE_CHECKIN)

ROLE_LABELS = {
    ROLE_ADMIN: "Administrator",
    ROLE_REGISTRATION: "Registration Operator",
    ROLE_CHECKIN: "Check-in Operator",
}


@dataclass(frozen=True)
class Paths:
    """All filesystem locations used by the application."""

    base_dir: Path
    data_dir: Path
    db_path: Path
    qr_dir: Path
    exports_dir: Path
    backups_dir: Path
    logs_dir: Path
    assets_dir: Path

    def ensure(self) -> None:
        for directory in (
            self.data_dir,
            self.qr_dir,
            self.exports_dir,
            self.backups_dir,
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def event_qr_dir(self, event_id: int) -> Path:
        path = self.qr_dir / f"event_{event_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path


def _resource_base() -> Path:
    """Find the real resource folder when running from a py2app bundle."""
    if getattr(sys, "frozen", False):
        resources = Path(sys.executable).parent.parent / "Resources"
        if resources.exists():
            return resources
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def default_paths() -> Paths:
    """Resolve paths, allowing an external data directory via environment variable."""
    base = _resource_base()
    env_data = os.environ.get("EVENTRA_DATA_DIR")
    data = Path(env_data).expanduser().resolve() if env_data else base / "data"
    return Paths(
        base_dir=base,
        data_dir=data,
        db_path=data / "eventra.db",
        qr_dir=data / "qr_codes",
        exports_dir=data / "exports",
        backups_dir=data / "backups",
        logs_dir=data / "logs",
        assets_dir=base / "assets",
    )
