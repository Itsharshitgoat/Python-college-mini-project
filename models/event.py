"""Event model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Event:
    event_id: int | None = None
    event_name: str = ""
    description: str = ""
    event_date: str = ""
    start_time: str = ""
    end_time: str = ""
    venue: str = ""
    capacity: int = 0
    registration_status: str = "DRAFT"
    checkin_status: str = "DISABLED"
    created_at: str = ""
    registered_count: int = 0
    attended_count: int = 0

    @classmethod
    def from_row(cls, row: Any) -> "Event":
        data = dict(row)
        registered = int(data.pop("registered_count", 0) or 0)
        attended = int(data.pop("attended_count", 0) or 0)
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(registered_count=registered, attended_count=attended, **fields)

    @property
    def pending_count(self) -> int:
        return max(self.registered_count - self.attended_count, 0)

    @property
    def status_label(self) -> str:
        return self.registration_status.replace("_", " ").title()
