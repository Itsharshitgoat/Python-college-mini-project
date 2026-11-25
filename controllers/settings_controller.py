"""Application settings operations exposed to the UI."""

from __future__ import annotations

from services.settings_service import SettingsService


class SettingsController:
    def __init__(self, service: SettingsService):
        self.service = service

    def get(self, key: str, default: str = "") -> str:
        return self.service.get(key, default)

    def get_int(self, key: str, default: int) -> int:
        return self.service.get_int(key, default)

    def set(self, key: str, value: str | int) -> None:
        self.service.set(key, value)

    def all(self) -> dict[str, str]:
        return self.service.all()
