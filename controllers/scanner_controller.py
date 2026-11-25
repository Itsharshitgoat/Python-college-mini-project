"""Scanner operations exposed to the UI."""

from __future__ import annotations

from services.checkin_service import CheckinService
from services.event_service import EventService


class ScannerController:
    def __init__(self, checkin: CheckinService, events: EventService):
        self.checkin = checkin
        self.events = events

    def event_options(self):
        result = self.events.list_events()
        return result.data if result.success else []

    def process_scan(self, payload: str, event_id: int, operator_id: int | None):
        return self.checkin.verify_and_checkin(payload, event_id, operator_id)
