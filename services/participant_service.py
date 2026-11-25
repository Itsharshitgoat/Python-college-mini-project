"""Participant validation and lookup rules."""

from __future__ import annotations

from models.participant import Participant
from repositories.participant_repository import ParticipantRepository
from utils.result import Result, ResultCode
from utils.validators import validate_participant_form


class ParticipantService:
    def __init__(self, participant_repo: ParticipantRepository):
        self.participants = participant_repo

    def validate(self, form: dict) -> str | None:
        return validate_participant_form(form)

    def search(self, query: str) -> Result:
        return Result.ok(data=self.participants.search(query))

    def get(self, participant_id: int) -> Result:
        participant = self.participants.get_by_id(participant_id)
        return (
            Result.ok(data=participant)
            if participant
            else Result.fail(ResultCode.NOT_FOUND, "Participant not found.")
        )

    def duplicate_warning(self, participant: Participant) -> str:
        return (
            f"An existing participant with phone {participant.phone} "
            f"({participant.full_name}) will be reused."
        )
