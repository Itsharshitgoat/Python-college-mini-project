"""Application settings, backup and password management."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog

from config import APP_NAME, APP_TAGLINE, APP_VERSION
from ui.components.dialogs import ChangePasswordDialog, MessageDialog
from ui.components.notification import notify
from ui.screens.base import ScreenBase
from ui.theme import (
    BORDER, MUTED, NAVY, SURFACE, TEXT, button_style, card_style, font,
)
from utils.file_utils import open_path


class SettingsScreen(ScreenBase):
    def __init__(self, master, ctx, nav, **kwargs):
        super().__init__(master, ctx, nav, "Settings", "Preferences, backup and application information")
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.can_manage = ctx.session.can("settings.manage")

        self._card("APPEARANCE", self._appearance_section)
        self._card("CAMERA & QR", self._camera_section)
        self._card("GENERAL", self._general_section)
        self._card("DATABASE", self._database_section)
        self._card("ABOUT", self._about_section)

    def _card(self, title: str, builder) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.body, **card_style())
        frame.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            frame, text=title, font=font(11, "bold"), text_color=MUTED, anchor="w"
        ).pack(anchor="w", padx=20, pady=(16, 6))
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 16))
        inner.grid_columnconfigure(1, weight=1)
        builder(inner, frame)
        return frame

    def _field(self, parent, row: int, key: str, label: str, value: str,
               placeholder: str = "", browse: bool = False) -> None:
        ctk.CTkLabel(
            parent, text=label, font=font(12), text_color=TEXT, anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=10, pady=6)
        entry = ctk.CTkEntry(
            parent, height=34, font=font(12), placeholder_text=placeholder
        )
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=6)
        entry.insert(0, value or "")
        if not self.can_manage:
            entry.configure(state="disabled")
        self.entries[key] = entry
        if browse:
            ctk.CTkButton(
                parent, text="Browse", width=80, height=34, font=font(11),
                command=lambda: self._browse(entry), **button_style("outline"),
            ).grid(row=row, column=2, padx=10)

    def _appearance_section(self, parent, frame) -> None:
        ctk.CTkLabel(
            parent, text="Theme", font=font(12), text_color=TEXT, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=6)
        current = self._setting("theme", "Light")
        self.theme_var = ctk.StringVar(value=current.title())
        combo = ctk.CTkComboBox(
            parent, values=["Light", "Dark"], variable=self.theme_var,
            state="readonly", height=34, font=font(12), width=160,
            command=lambda *_: self._save_theme(),
        )
        combo.grid(row=0, column=1, sticky="w", padx=10, pady=6)
        if not self.can_manage:
            combo.configure(state="disabled")

    def _camera_section(self, parent, frame) -> None:
        self._field(parent, 0, "camera_index", "Camera index", self._setting("camera_index", "0"))
        self._field(parent, 1, "camera_width", "Frame width", self._setting("camera_width", "640"))
        self._field(parent, 2, "camera_height", "Frame height", self._setting("camera_height", "480"))
        self._field(parent, 3, "qr_image_size", "QR image size", self._setting("qr_image_size", "320"))
        self._save_button(parent, 4, "Save Camera & QR Settings", self._save_camera)

    def _general_section(self, parent, frame) -> None:
        self._field(
            parent, 0, "organization_name", "Organization name",
            self._setting("organization_name", "EVENTRA Organization"),
        )
        self._field(
            parent, 1, "export_directory", "Default export folder",
            self._setting("export_directory", ""), "Optional", browse=True,
        )
        self._save_button(parent, 2, "Save General Settings", self._save_general)
        ctk.CTkButton(
            parent, text="Change Password", height=34, font=font(11, "bold"),
            command=self._change_password, **button_style("outline"),
        ).grid(row=2, column=2, padx=10, pady=6)

    def _database_section(self, parent, frame) -> None:
        ctk.CTkLabel(
            parent, text=f"Database file: {self.ctx.paths.db_path.name}",
            font=font(12), text_color=TEXT, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=6)
        backups = self.ctx.report_controller.list_backups()
        ctk.CTkLabel(
            parent, text=f"Existing backups: {len(backups)}",
            font=font(11), text_color=MUTED, anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
        if self.ctx.session.can("backup"):
            ctk.CTkButton(
                parent, text="Backup Database", height=36, font=font(12, "bold"),
                command=self._backup, **button_style("primary"),
            ).grid(row=2, column=0, sticky="w", padx=10, pady=10)
            ctk.CTkButton(
                parent, text="Open Backup Folder", height=36, font=font(12),
                command=lambda: open_path(self.ctx.paths.backups_dir),
                **button_style("outline"),
            ).grid(row=2, column=1, sticky="w", padx=10, pady=10)

    def _about_section(self, parent, frame) -> None:
        lines = (
            f"{APP_NAME} v{APP_VERSION}",
            APP_TAGLINE,
            "Offline-first • SQLite • Secure QR tokens",
        )
        for index, line in enumerate(lines):
            ctk.CTkLabel(
                parent, text=line,
                font=font(13, "bold") if index == 0 else font(11),
                text_color=NAVY if index == 0 else MUTED, anchor="w",
            ).grid(row=index, column=0, columnspan=3, sticky="w", padx=10, pady=(4, 0))

    def _save_button(self, parent, row: int, text: str, command) -> None:
        button = ctk.CTkButton(
            parent, text=text, height=34, font=font(11, "bold"),
            command=command, **button_style("primary"),
        )
        button.grid(row=row, column=2, padx=10, pady=6)
        if not self.can_manage:
            button.configure(state="disabled")

    def _setting(self, key: str, default: str) -> str:
        return self.ctx.settings_controller.get(key, default)

    def _save_setting(self, key: str, value: str) -> None:
        self.ctx.settings_controller.set(key, value)

    def _save_theme(self) -> None:
        import customtkinter as ctk

        theme = self.theme_var.get()
        ctk.set_appearance_mode(theme)
        self._save_setting("theme", theme)
        notify(self, f"Theme set to {theme}.", "success")

    def _save_camera(self) -> None:
        for key in ("camera_index", "camera_width", "camera_height", "qr_image_size"):
            value = self.entries[key].get().strip()
            if not value.isdigit():
                MessageDialog(self, "Settings", f"{key} must be a number.", "error")
                return
        for key in ("camera_index", "camera_width", "camera_height", "qr_image_size"):
            self._save_setting(key, self.entries[key].get().strip())
        notify(self, "Camera and QR settings saved.", "success")

    def _save_general(self) -> None:
        self._save_setting("organization_name", self.entries["organization_name"].get().strip())
        self._save_setting("export_directory", self.entries["export_directory"].get().strip())
        notify(self, "General settings saved.", "success")

    def _browse(self, entry: ctk.CTkEntry) -> None:
        directory = filedialog.askdirectory(parent=self)
        if directory:
            entry.delete(0, "end")
            entry.insert(0, directory)

    def _backup(self) -> None:
        result = self.ctx.report_controller.create_backup()
        if not result.success:
            notify(self, result.message, "error")
            return
        MessageDialog(
            self, "Backup complete", f"Database backed up to:\n{result.data['path']}"
        )
        self.refresh()

    def _change_password(self) -> None:
        def save(current: str, new: str, confirm: str) -> bool:
            if new != confirm:
                MessageDialog(self, "Change Password", "New passwords do not match.", "error")
                return False
            result = self.ctx.auth_controller.change_password(
                self.ctx.session.user_id, current, new
            )
            if not result.success:
                MessageDialog(self, "Change Password", result.message, "error")
                return False
            notify(self, "Password changed successfully.", "success")
            return True

        ChangePasswordDialog(self, save)

    def refresh(self) -> None:
        # Settings are loaded at construction; no dynamic data to refresh.
        pass
