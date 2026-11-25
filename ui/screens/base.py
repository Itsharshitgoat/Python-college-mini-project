"""Shared screen scaffolding."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.context import AppContext
from ui.theme import BG, MUTED, TEXT, font


class ScreenBase(ctk.CTkFrame):
    def __init__(self, master, ctx: AppContext, nav, title: str, subtitle: str = ""):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.ctx = ctx
        self.nav = nav

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=28, pady=(24, 12))
        head.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(
            head, text=title, font=font(24, "bold"), text_color=TEXT, anchor="w"
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = ctk.CTkLabel(
            head, text=subtitle, font=font(12), text_color=MUTED, anchor="w"
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.actions = ctk.CTkFrame(head, fg_color="transparent")
        self.actions.grid(row=0, column=1, rowspan=2, sticky="e")

        self.body = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color="#CBD5E1"
        )
        self.body.pack(fill="both", expand=True, padx=28, pady=(4, 24))
        self.body.grid_columnconfigure(0, weight=1)

    def set_heading(self, title: str, subtitle: str = "") -> None:
        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)

    def add_action(self, text: str, command: Callable, kind: str = "primary", width: int = 130):
        from ui.theme import button_style

        ctk.CTkButton(
            self.actions, text=text, width=width, height=36, font=font(12, "bold"),
            command=command, **button_style(kind),
        ).pack(side="left", padx=(8, 0))
