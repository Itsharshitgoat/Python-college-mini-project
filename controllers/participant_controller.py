"""Participant operations exposed to the UI."""

from __future__ import annotations

from services.participant_service import ParticipantService


class ParticipantController:
    def __init__(self, service: ParticipantService):
        self.service = service

    def search(self, query: str):
        return self.service.search(query)

    def get(self, participant_id: int):
        return self.service.get(participant_id)
