"""Main application shell: sidebar, header and switching content."""

from __future__ import annotations

import customtkinter as ctk

from core.context import AppContext
from core.navigation import NavigationManager
from ui.components.header import Header
from ui.components.notification import notify
from ui.components.sidebar import Sidebar
from ui.theme import BG

SCREEN_TITLES = {
    "dashboard": ("Dashboard", "Overview of your event operations"),
    "events": ("Events", "Create and manage events"),
    "event_details": ("Event Details", "Event overview and registrations"),
    "registration": ("Registration", "Register participants and issue tickets"),
    "scanner": ("QR Scanner", "Verify tickets and record attendance"),
    "attendance": ("Attendance", "Check-in records and participant status"),
    "reports": ("Analytics", "Attendance insights and reports"),
    "users": ("User Management", "Accounts and permissions"),
    "settings": ("Settings", "Application preferences"),
}


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, ctx: AppContext, app):
        super().__init__(master, fg_color=BG)
        self.ctx = ctx
        self.app = app
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = Sidebar(
            self, ctx, on_navigate=self.navigate, on_logout=app.logout
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")

        self.header = Header(
            self, ctx, on_refresh=self.refresh, on_logout=app.logout
        )
        self.header.grid(row=0, column=1, sticky="ew")

        content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        content.grid(row=1, column=1, sticky="nsew")
        self.navigation = NavigationManager(ctx, content)

        self.navigate("dashboard")
        self._schedule_idle_check()

    def navigate(self, key: str, **screen_context) -> ctk.CTkFrame:
        screen = self.navigation.navigate(key, **screen_context)
        title, subtitle = SCREEN_TITLES.get(key, (key.title(), ""))
        self.header.set_title(title, subtitle)
        label_hint = None
        if key == "registration":
            label_hint = (
                "Participants" if screen_context.get("mode") == "participants"
                else "Registration"
            )
        active_key = "events" if key == "event_details" else key
        self.sidebar.set_active(active_key, label_hint)

        if key == "events" and screen_context.get("open_dialog"):
            screen._create()
        if key == "event_details" and screen_context.get("open_registration"):
            screen._open_registration()
        return screen

    def refresh(self) -> None:
        self.ctx.session.touch()
        self.navigation.refresh()

    def stop_camera(self) -> None:
        self.navigation.shutdown()

    def _schedule_idle_check(self) -> None:
        if self.winfo_exists():
            if self.ctx.session.is_idle():
                notify(self, "Session timed out. Please sign in again.", "warning")
                self.app.logout()
                return
            self.after(60_000, self._schedule_idle_check)
