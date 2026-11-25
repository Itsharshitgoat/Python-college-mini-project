"""Registration and ticket operations exposed to the UI."""

from __future__ import annotations

from services.qr_service import QrService
from services.registration_service import RegistrationService


class RegistrationController:
    def __init__(self, service: RegistrationService, qr: QrService):
        self.service = service
        self.qr = qr

    def register(self, form: dict, user_id: int | None = None):
        return self.service.register(form, user_id)

    def reissue(self, registration_id: int, user_id: int | None = None):
        return self.service.reissue_ticket(registration_id, user_id)

    def cancel(self, registration_id: int, user_id: int | None = None):
        return self.service.cancel(registration_id, user_id)

    def remove(self, registration_id: int, user_id: int | None = None):
        return self.service.delete_registration(registration_id, user_id)

    def list_for_event(self, event_id: int, search: str = "", filter_status: str = "all"):
        return self.service.list_for_event(event_id, search, filter_status)

    def list_for_participant(self, participant_id: int):
        return self.service.list_for_participant(participant_id)

    def get(self, registration_id: int):
        return self.service.get(registration_id)
