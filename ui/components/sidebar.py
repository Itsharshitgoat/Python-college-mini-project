"""Left navigation sidebar."""

from __future__ import annotations

import customtkinter as ctk

from core.context import AppContext
from ui.theme import NAVY, NAVY_LIGHT, TEAL, font

NAV_SECTIONS = (
    ("OVERVIEW", (
        ("dashboard", "▦", "Dashboard", "dashboard", {}),
    )),
    ("MANAGEMENT", (
        ("events", "▤", "Events", "events.view", {}),
        ("registration", "＋", "Participants", "participants.manage", {"mode": "participants"}),
        ("registration", "✎", "Registration", "registrations.manage", {}),
    )),
    ("OPERATIONS", (
        ("scanner", "▣", "QR Scanner", "scanner", {}),
        ("attendance", "☑", "Attendance", "attendance.view", {}),
    )),
    ("REPORTS", (
        ("reports", "◔", "Analytics", "reports.view", {}),
    )),
    ("SYSTEM", (
        ("users", "♙", "User Management", "users.manage", {}),
        ("settings", "⚙", "Settings", "settings.view", {}),
    )),
)


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, ctx: AppContext, on_navigate, on_logout, **kwargs):
        super().__init__(
            master, fg_color=NAVY, corner_radius=0, width=232, **kwargs
        )
        self.ctx = ctx
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self._buttons: dict[tuple[str, str], ctk.CTkButton] = {}

        logo = ctk.CTkFrame(self, fg_color="transparent", height=92)
        logo.pack(fill="x", padx=18, pady=(20, 8))
        ctk.CTkLabel(logo, text="EVENTRA", font=font(22, "bold"), text_color="white").pack(
            anchor="w"
        )
        ctk.CTkLabel(
            logo, text="EVENT MANAGEMENT", font=font(10), text_color="#93C5FD"
        ).pack(anchor="w")

        scroller = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=NAVY_LIGHT
        )
        scroller.pack(fill="both", expand=True, padx=10, pady=6)
        scroller.grid_columnconfigure(0, weight=1)

        row = 0
        for section_title, items in NAV_SECTIONS:
            visible = [
                item for item in items if self.ctx.session.can(item[3])
            ]
            if not visible:
                continue
            ctk.CTkLabel(
                scroller, text=section_title, font=font(10, "bold"),
                text_color="#64748B", anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=12, pady=(16, 6))
            row += 1
            for key, icon, label, permission, context in visible:
                button = ctk.CTkButton(
                    scroller,
                    text=f"  {icon}    {label}",
                    font=font(13),
                    anchor="w",
                    fg_color="transparent",
                    hover_color=NAVY_LIGHT,
                    text_color="#CBD5E1",
                    corner_radius=8,
                    height=38,
                    command=lambda k=key, c=context: self.on_navigate(k, **c),
                )
                button.grid(row=row, column=0, sticky="ew", pady=2)
                self._buttons[(key, label)] = button
                row += 1

        footer = ctk.CTkFrame(self, fg_color="#0F1C3F", corner_radius=12)
        footer.pack(fill="x", padx=14, pady=14)
        ctk.CTkLabel(
            footer, text=self.ctx.session.display_name,
            font=font(12, "bold"), text_color="white", anchor="w",
        ).pack(fill="x", padx=12, pady=(12, 0))
        ctk.CTkLabel(
            footer, text=self.ctx.session.role_label,
            font=font(10), text_color="#93C5FD", anchor="w",
        ).pack(fill="x", padx=12)
        ctk.CTkButton(
            footer, text="Sign out", font=font(11), height=28,
            fg_color="transparent", hover_color=NAVY_LIGHT,
            text_color="#FCA5A5", command=self.on_logout,
        ).pack(fill="x", padx=8, pady=(8, 10))

    def set_active(self, key: str, label_hint: str | None = None) -> None:
        for (item_key, item_label), button in self._buttons.items():
            active = item_key == key and (label_hint is None or item_label == label_hint)
            button.configure(
                fg_color=TEAL if active else "transparent",
                text_color="white" if active else "#CBD5E1",
            )
