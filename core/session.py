"""Authenticated session and role-based permissions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from config import ROLE_ADMIN, ROLE_CHECKIN, ROLE_REGISTRATION, ROLE_LABELS
from models.user import User
from utils.date_utils import utc_now_iso

PERMISSIONS = {
    "dashboard": (ROLE_ADMIN, ROLE_REGISTRATION, ROLE_CHECKIN),
    "events.view": (ROLE_ADMIN, ROLE_REGISTRATION, ROLE_CHECKIN),
    "events.manage": (ROLE_ADMIN,),
    "participants.manage": (ROLE_ADMIN, ROLE_REGISTRATION),
    "registrations.manage": (ROLE_ADMIN, ROLE_REGISTRATION),
    "tickets.view": (ROLE_ADMIN, ROLE_REGISTRATION),
    "scanner": (ROLE_ADMIN, ROLE_CHECKIN),
    "attendance.view": (ROLE_ADMIN, ROLE_REGISTRATION, ROLE_CHECKIN),
    "attendance.manual": (ROLE_ADMIN,),
    "reports.view": (ROLE_ADMIN, ROLE_REGISTRATION),
    "reports.export": (ROLE_ADMIN, ROLE_REGISTRATION),
    "users.manage": (ROLE_ADMIN,),
    "settings.view": (ROLE_ADMIN, ROLE_REGISTRATION, ROLE_CHECKIN),
    "settings.manage": (ROLE_ADMIN,),
    "backup": (ROLE_ADMIN,),
}

SESSION_TIMEOUT_SECONDS = 30 * 60


@dataclass
class Session:
    user: User | None = None
    logged_in_at: str = ""
    _last_activity: float = field(default_factory=time.time)

    def login(self, user: User) -> None:
        self.user = user
        self.logged_in_at = utc_now_iso()
        self.touch()

    def logout(self) -> None:
        self.user = None
        self.logged_in_at = ""

    def touch(self) -> None:
        self._last_activity = time.time()

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None and bool(self.user.is_active)

    @property
    def user_id(self) -> int | None:
        return self.user.user_id if self.user else None

    @property
    def role(self) -> str | None:
        return self.user.role if self.user else None

    @property
    def display_name(self) -> str:
        if not self.user:
            return "Guest"
        return self.user.full_name or self.user.username

    @property
    def role_label(self) -> str:
        return ROLE_LABELS.get(self.role or "", "Guest")

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def can(self, permission: str) -> bool:
        if not self.is_authenticated:
            return False
        return self.role in PERMISSIONS.get(permission, ())

    def is_idle(self) -> bool:
        return (time.time() - self._last_activity) > SESSION_TIMEOUT_SECONDS
