"""Lightweight schema version management."""

from __future__ import annotations

from database.connection import Database

CURRENT_SCHEMA_VERSION = 1


def current_version(db: Database) -> int:
    value = db.scalar(
        "SELECT setting_value FROM application_settings WHERE setting_key = 'schema_version'"
    )
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0


def migrate(db: Database) -> None:
    """Apply future schema upgrades here; schema.sql handles initial creation."""
    version = current_version(db)
    while version < CURRENT_SCHEMA_VERSION:
        version += 1
        db.execute(
            "INSERT OR REPLACE INTO application_settings (setting_key, setting_value) VALUES (?, ?)",
            ("schema_version", str(version)),
        )
