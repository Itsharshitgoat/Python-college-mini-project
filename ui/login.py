"""Sign-in screen."""

from __future__ import annotations

import customtkinter as ctk

from config import APP_NAME, APP_TAGLINE, APP_VERSION
from core.context import AppContext
from ui.theme import BORDER, ERROR, NAVY, SURFACE, TEXT, TEAL, button_style, font


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, ctx: AppContext, on_success):
        super().__init__(master, fg_color="#F5F7FA")
        self.ctx = ctx
        self.on_success = on_success
        self.pack(fill="both", expand=True)

        header = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0, height=150)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text=APP_NAME, font=font(38, "bold"), text_color="white"
        ).pack(pady=(34, 0))
        ctk.CTkLabel(
            header, text="EVENT MANAGEMENT SYSTEM",
            font=font(11, "bold"), text_color="#99CEFF",
        ).pack(pady=(6, 0))

        card = ctk.CTkFrame(
            self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER
        )
        card.pack(fill="both", expand=True, padx=34, pady=(22, 30))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            card, text="Welcome Back", font=font(22, "bold"), text_color=TEXT
        ).pack(pady=(28, 2))
        ctk.CTkLabel(
            card, text="Sign in to continue to EVENTRA", font=font(11), text_color="#64748B"
        ).pack()

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=34, pady=(20, 8))
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form, text="USERNAME", font=font(10, "bold"), text_color="#64748B", anchor="w"
        ).grid(row=0, column=0, sticky="w")
        self.username = ctk.CTkEntry(
            form, height=42, font=font(13), placeholder_text="Enter your username"
        )
        self.username.grid(row=1, column=0, sticky="ew", pady=(4, 14))

        ctk.CTkLabel(
            form, text="PASSWORD", font=font(10, "bold"), text_color="#64748B", anchor="w"
        ).grid(row=2, column=0, sticky="w")
        self.password = ctk.CTkEntry(
            form, height=42, font=font(13), placeholder_text="Enter your password", show="*"
        )
        self.password.grid(row=3, column=0, sticky="ew", pady=(4, 6))

        options = ctk.CTkFrame(form, fg_color="transparent")
        options.grid(row=4, column=0, sticky="ew", pady=(2, 8))
        self.show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options, text="Show password", variable=self.show_var,
            font=font(11), command=self._toggle_password,
        ).pack(side="left")
        remember_value = self.ctx.settings_controller.get("remembered_username")
        self.remember_var = ctk.BooleanVar(value=bool(remember_value))
        ctk.CTkCheckBox(
            options, text="Remember username", variable=self.remember_var,
            font=font(11),
        ).pack(side="right")
        if remember_value:
            self.username.insert(0, str(remember_value))

        self.error_label = ctk.CTkLabel(
            form, text="", font=font(11), text_color=ERROR, anchor="w"
        )
        self.error_label.grid(row=5, column=0, sticky="w")

        ctk.CTkButton(
            form, text="SIGN IN", height=44, font=font(13, "bold"),
            command=self._submit, **button_style("primary"),
        ).grid(row=6, column=0, sticky="ew", pady=(8, 4))

        ctk.CTkLabel(
            self, text=f"{APP_NAME} v{APP_VERSION}  •  Offline Desktop Application",
            font=font(10), text_color="#94A3B8",
        ).pack(side="bottom", pady=12)

        self.password.bind("<Return>", lambda _event: self._submit())
        self.username.focus_set()

    def _toggle_password(self) -> None:
        self.password.configure(show="" if self.show_var.get() else "*")

    def _submit(self) -> None:
        username = self.username.get().strip()
        password = self.password.get()
        self.error_label.configure(text="")
        if not username or not password:
            self.error_label.configure(text="Enter both username and password.")
            return
        result = self.ctx.auth_controller.login(username, password)
        if not result.success:
            self.error_label.configure(text=result.message)
            self.password.delete(0, "end")
            return
        self.ctx.settings_controller.set(
            "remembered_username",
            username if self.remember_var.get() else "",
        )
        self.on_success(result.data)
