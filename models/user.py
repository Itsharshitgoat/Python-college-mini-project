"""Application user model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import ROLE_LABELS


@dataclass
class User:
    user_id: int | None = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = ""
    is_active: int = 1
    created_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "User":
        data = dict(row)
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)
