"""Application preference rules and typed setting access."""

from __future__ import annotations

from repositories.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self, settings: SettingsRepository):
        self.settings = settings

    def get(self, key: str, default: str = "") -> str:
        return self.settings.get(key, default)

    def get_int(self, key: str, default: int) -> int:
        value = self.settings.get(key)
        try:
            return int(value) if value else default
        except (TypeError, ValueError):
            return default

    def set(self, key: str, value: str | int) -> None:
        self.settings.set(key, str(value))

    def all(self) -> dict[str, str]:
        return self.settings.all()
