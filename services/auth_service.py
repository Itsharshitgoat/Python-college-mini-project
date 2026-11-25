"""Authentication, account management and password rules."""

from __future__ import annotations

from config import ROLES
from repositories.audit_repository import AuditRepository
from repositories.user_repository import UserRepository
from utils.date_utils import utc_now_iso
from utils.result import Result, ResultCode
from utils.security import hash_password, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        self.users = user_repo
        self.audit = audit_repo

    def login(self, username: str, password: str) -> Result:
        user = self.users.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            return Result.fail(
                ResultCode.UNAUTHORIZED, "Invalid username or password."
            )
        if not user.is_active:
            return Result.fail(
                ResultCode.UNAUTHORIZED, "This account has been deactivated."
            )
        self.audit.log("LOGIN", f"User '{user.username}' signed in", user_id=user.user_id)
        return Result.ok("Welcome back.", user)

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> Result:
        user = self.users.get_by_id(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            return Result.fail(ResultCode.UNAUTHORIZED, "Current password is incorrect.")
        if len(new_password) < 6:
            return Result.fail(
                ResultCode.INVALID_INPUT, "New password must be at least 6 characters."
            )
        self.users.set_password(user_id, hash_password(new_password))
        self.audit.log("PASSWORD_CHANGED", f"User ID {user_id}", user_id=user_id)
        return Result.ok("Password changed successfully.")

    def create_user(self, form: dict, creator_id: int | None = None) -> Result:
        username = (form.get("username") or "").strip()
        password = form.get("password") or ""
        role = form.get("role")
        if not username or len(username) < 3:
            return Result.fail(
                ResultCode.INVALID_INPUT, "Username must be at least 3 characters."
            )
        if len(password) < 6:
            return Result.fail(
                ResultCode.INVALID_INPUT, "Password must be at least 6 characters."
            )
        if role not in ROLES:
            return Result.fail(ResultCode.INVALID_INPUT, "Select a valid role.")
        if self.users.get_by_username(username):
            return Result.fail(ResultCode.DUPLICATE_REGISTRATION, "Username already exists.")

        user_id = self.users.create(
            {
                "username": username,
                "password_hash": hash_password(password),
                "full_name": (form.get("full_name") or "").strip(),
                "role": role,
                "created_at": utc_now_iso(),
            }
        )
        self.audit.log(
            "USER_CREATED", f"Created '{username}' ({role})", user_id=creator_id
        )
        return Result.ok("User account created.", {"user_id": user_id})

    def set_active(self, user_id: int, active: bool, creator_id: int | None = None) -> Result:
        user = self.users.get_by_id(user_id)
        if not user:
            return Result.fail(ResultCode.NOT_FOUND, "User not found.")
        self.users.set_active(user_id, active)
        self.audit.log(
            "USER_STATUS_CHANGED",
            f"'{user.username}' -> {'active' if active else 'inactive'}",
            user_id=creator_id,
        )
        return Result.ok("User status updated.")

    def update_user(self, user_id: int, form: dict, creator_id: int | None = None) -> Result:
        if not self.users.get_by_id(user_id):
            return Result.fail(ResultCode.NOT_FOUND, "User not found.")
        if form.get("role") and form["role"] not in ROLES:
            return Result.fail(ResultCode.INVALID_INPUT, "Select a valid role.")
        self.users.update(user_id, form)
        self.audit.log("USER_UPDATED", f"User ID {user_id}", user_id=creator_id)
        return Result.ok("User updated.")

    def list_users(self) -> Result:
        return Result.ok(data=self.users.get_all())
