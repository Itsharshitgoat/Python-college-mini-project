"""Event operations exposed to the UI."""

from __future__ import annotations

from services.event_service import EventService


class EventController:
    def __init__(self, service: EventService):
        self.service = service

    def create(self, form: dict, user_id: int | None = None):
        return self.service.create(form, user_id)

    def update(self, event_id: int, form: dict, user_id: int | None = None):
        return self.service.update(event_id, form, user_id)

    def set_status(self, event_id: int, column: str, value: str, user_id=None):
        return self.service.set_status(event_id, column, value, user_id)

    def list(self, search: str = "", status: str | None = None):
        return self.service.list_events(search, status)

    def get(self, event_id: int):
        return self.service.get_event(event_id)

    def delete(self, event_id: int, user_id=None):
        return self.service.delete(event_id, user_id)
