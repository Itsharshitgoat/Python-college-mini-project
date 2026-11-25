"""Top header bar."""

from __future__ import annotations

import customtkinter as ctk

from core.context import AppContext
from ui.theme import BORDER, MUTED, NAVY, SURFACE, TEXT, button_style, font


class Header(ctk.CTkFrame):
    def __init__(self, master, ctx: AppContext, on_refresh, on_logout, **kwargs):
        super().__init__(
            master, fg_color=SURFACE, corner_radius=0, height=76, **kwargs
        )
        self.ctx = ctx
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, minsize=76)
        self.grid_propagate(False)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=28, pady=10)
        self.title_label = ctk.CTkLabel(
            left, text="Dashboard", font=font(20, "bold"), text_color=TEXT, anchor="w"
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(
            left, text="Overview of your event operations",
            font=font(11), text_color=MUTED, anchor="w",
        )
        self.subtitle_label.pack(anchor="w")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=24, pady=10)

        badge = ctk.CTkFrame(right, fg_color="#E8EDF7", corner_radius=16, height=32)
        badge.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            badge, text=f"  {ctx.session.role_label}  ",
            font=font(11, "bold"), text_color=NAVY,
        ).pack()

        ctk.CTkButton(
            right, text="↻ Refresh", width=92, height=34,
            font=font(12), command=on_refresh, **button_style("outline"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            right, text="Sign out", width=80, height=34,
            font=font(12), command=on_logout, **button_style("secondary"),
        ).pack(side="left")

    def set_title(self, title: str, subtitle: str = "") -> None:
        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)
