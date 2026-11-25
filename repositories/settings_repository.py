"""Application settings persistence."""

from __future__ import annotations

from repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    def get(self, key: str, default: str = "") -> str:
        value = self.db.scalar(
            "SELECT setting_value FROM application_settings WHERE setting_key = ?",
            (key,),
        )
        return str(value) if value not in (None, "") else default

    def set(self, key: str, value: str) -> None:
        self.db.execute(
            """INSERT OR REPLACE INTO application_settings
               (setting_key, setting_value) VALUES (?, ?)""",
            (key, str(value)),
        )

    def all(self) -> dict[str, str]:
        rows = self.db.query_all(
            "SELECT setting_key, setting_value FROM application_settings"
        )
        return {row["setting_key"]: str(row["setting_value"]) for row in rows}
