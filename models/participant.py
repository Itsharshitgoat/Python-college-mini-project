"""Participant model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Participant:
    participant_id: int | None = None
    full_name: str = ""
    email: str = ""
    phone: str = ""
    college: str = ""
    department: str = ""
    year: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "Participant":
        data = dict(row)
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)
