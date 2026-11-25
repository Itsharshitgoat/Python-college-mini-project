"""User and role management (administrator only)."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.data_table import DataTable
from ui.components.dialogs import ChangePasswordDialog, CreateUserDialog, MessageDialog
from ui.components.notification import notify
from ui.screens.base import ScreenBase
from ui.theme import TEXT, button_style, card_style, font
from utils.date_utils import format_date


class UsersScreen(ScreenBase):
    def __init__(self, master, ctx, nav, **kwargs):
        super().__init__(master, ctx, nav, "User Management", "Accounts, roles and permissions")
        if not ctx.session.can("users.manage"):
            ctk.CTkLabel(
                self.body, text="Your role does not have permission to manage users.",
                font=font(14), text_color=TEXT,
            ).pack(pady=40)
            return

        self.add_action("＋ New User", self._create, "primary", 110)
        self._users: list = []

        self.table = DataTable(
            self.body,
            columns=[("Username", 2), ("Name", 3), ("Role", 3), ("Status", 2), ("Created", 2)],
            on_select=self._on_select,
            empty_text="No user accounts found.",
        )
        self.table.pack(fill="both", expand=True)

        actions = ctk.CTkFrame(self.body, **card_style())
        actions.pack(fill="x", pady=(12, 0))
        self.toggle_btn = ctk.CTkButton(
            actions, text="Activate / Deactivate", height=34, font=font(12),
            command=self._toggle, state="disabled", **button_style("outline"),
        )
        self.change_btn = ctk.CTkButton(
            actions, text="Change My Password", height=34, font=font(12),
            command=self._change_password, **button_style("secondary"),
        )
        self.toggle_btn.pack(side="left", padx=(12, 8), pady=12)
        self.change_btn.pack(side="left", padx=8, pady=12)

    def refresh(self):
        if not self.ctx.session.can("users.manage"):
            return
        result = self.ctx.auth_controller.list_users()
        self._users = result.data or []
        self.table.set_rows(
            [
                (
                    user.username,
                    user.full_name or "-",
                    user.role_label,
                    "ACTIVE" if user.is_active else "INACTIVE",
                    format_date(user.created_at),
                )
                for user in self._users
            ]
        )
        self.selected_id = None
        self.toggle_btn.configure(state="disabled")

    def _on_select(self, index: int) -> None:
        if 0 <= index < len(self._users):
            self.selected_id = self._users[index].user_id
            self.toggle_btn.configure(state="normal")

    def _create(self) -> None:
        def save(form: dict) -> bool:
            result = self.ctx.auth_controller.create_user(form, self.ctx.session.user_id)
            if not result.success:
                MessageDialog(self, "Could not create user", result.message, "error")
                return False
            notify(self, "User account created.", "success")
            self.refresh()
            return True

        CreateUserDialog(self, save)

    def _toggle(self) -> None:
        user = next((u for u in self._users if u.user_id == self.selected_id), None)
        if not user:
            return
        if user.user_id == self.ctx.session.user_id:
            notify(self, "You cannot deactivate your own account.", "warning")
            return
        result = self.ctx.auth_controller.set_active(
            user.user_id, not bool(user.is_active), self.ctx.session.user_id
        )
        notify(self, result.message, "success" if result.success else "error")
        self.refresh()

    def _change_password(self) -> None:
        def save(current: str, new: str, confirm: str) -> bool:
            if new != confirm:
                MessageDialog(self, "Change Password", "New passwords do not match.", "error")
                return False
            result = self.ctx.auth_controller.change_password(self.ctx.session.user_id, current, new)
            if not result.success:
                MessageDialog(self, "Change Password", result.message, "error")
                return False
            notify(self, "Password changed successfully.", "success")
            return True

        ChangePasswordDialog(self, save)
