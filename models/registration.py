"""Registration model (the link between a participant and an event)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Registration:
    registration_id: int | None = None
    participant_id: int = 0
    event_id: int = 0
    qr_token_hash: str = ""
    registration_status: str = "ACTIVE"
    registered_at: str = ""
    ticket_path: str = ""

    # Joined / display-only fields
    full_name: str = ""
    email: str = ""
    phone: str = ""
    college: str = ""
    department: str = ""
    year: str = ""
    event_name: str = ""
    event_date: str = ""
    venue: str = ""
    event_registration_status: str = ""
    event_checkin_status: str = ""
    attendance_id: int | None = None
    checked_in_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "Registration":
        data = dict(row)
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)

    @property
    def code(self) -> str:
        return f"REG-{self.registration_id:06d}" if self.registration_id else "REG-??????"

    @property
    def is_present(self) -> bool:
        return self.attendance_id is not None
