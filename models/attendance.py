"""Attendance (check-in) model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Attendance:
    attendance_id: int | None = None
    registration_id: int = 0
    operator_id: int | None = None
    checked_in_at: str = ""
    check_in_status: str = "PRESENT"

    # Joined / display-only fields
    full_name: str = ""
    phone: str = ""
    event_name: str = ""
    event_date: str = ""
    registration_code: str = ""
    operator_name: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "Attendance":
        data = dict(row)
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)
