"""Dashboard metric card."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import BORDER, MUTED, NAVY, SURFACE, TEXT, TEAL, card_style, font


class StatCard(ctk.CTkFrame):
    def __init__(self, master, label: str, value, icon: str = "◆", accent: str = TEAL,
                 hint: str = "", **kwargs):
        super().__init__(master, **card_style(), **kwargs)
        self.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=10, width=34, height=34)
        badge.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 0))
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text=icon, font=font(16, "bold"), text_color="white").place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(
            self, text=label.upper(), font=font(11, "bold"), text_color=MUTED, anchor="w"
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(14, 0))

        self.value_label = ctk.CTkLabel(
            self, text=str(value), font=font(30, "bold"), text_color=accent, anchor="w"
        )
        self.value_label.grid(row=2, column=0, sticky="ew", padx=18, pady=(2, 4))

        self.hint_label = None
        if hint:
            self.hint_label = ctk.CTkLabel(
                self, text=hint, font=font(11), text_color=MUTED, anchor="w"
            )
            self.hint_label.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 16))
        else:
            self.grid_rowconfigure(3, minsize=16)

    def set_value(self, value, accent: str | None = None, hint: str | None = None) -> None:
        """Update a card in place instead of destroying and rebuilding it."""
        self.value_label.configure(text=str(value))
        if accent:
            self.value_label.configure(text_color=accent)
        if hint is not None and self.hint_label is not None:
            self.hint_label.configure(text=hint)
