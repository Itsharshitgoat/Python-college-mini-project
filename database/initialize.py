"""Create the database, schema, defaults and administrator account."""

from __future__ import annotations

from pathlib import Path

from config import APP_VERSION, Paths, ROLE_ADMIN
from database.connection import Database
from utils.date_utils import utc_now_iso
from utils.security import hash_password

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin@123"
DEFAULT_ADMIN_FULL_NAME = "Administrator"

DEFAULT_SETTINGS = {
    "organization_name": "EVENTRA Organization",
    "theme": "Light",
    "camera_index": "0",
    "camera_width": "640",
    "camera_height": "480",
    "qr_image_size": "320",
    "export_directory": "",
    "schema_version": "1",
}


def initialize_database(db: Database, paths: Paths) -> None:
    paths.ensure()
    conn = db.connect()
    schema_path = paths.base_dir / "database" / "schema.sql"
    if not schema_path.exists():
        schema_path = Path(__file__).with_name("schema.sql")
    conn.executescript(schema_path.read_text())
    conn.execute("PRAGMA journal_mode = WAL")
    conn.commit()

    for key, value in DEFAULT_SETTINGS.items():
        db.execute(
            "INSERT OR IGNORE INTO application_settings (setting_key, setting_value) VALUES (?, ?)",
            (key, value),
        )

    if db.scalar("SELECT COUNT(*) FROM users") == 0:
        db.execute(
            """INSERT INTO users (username, password_hash, full_name, role, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (
                DEFAULT_ADMIN_USERNAME,
                hash_password(DEFAULT_ADMIN_PASSWORD),
                DEFAULT_ADMIN_FULL_NAME,
                ROLE_ADMIN,
                utc_now_iso(),
            ),
        )


def app_version() -> str:
    return APP_VERSION
