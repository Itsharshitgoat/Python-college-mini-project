"""Authentication and account operations exposed to the UI."""

from __future__ import annotations

from services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService):
        self.service = service

    def login(self, username: str, password: str):
        return self.service.login(username, password)

    def change_password(self, user_id: int, current_password: str, new_password: str):
        return self.service.change_password(user_id, current_password, new_password)

    def create_user(self, form: dict, creator_id: int | None = None):
        return self.service.create_user(form, creator_id)

    def set_active(self, user_id: int, active: bool, creator_id: int | None = None):
        return self.service.set_active(user_id, active, creator_id)

    def update_user(self, user_id: int, form: dict, creator_id: int | None = None):
        return self.service.update_user(user_id, form, creator_id)

    def list_users(self):
        return self.service.list_users()
