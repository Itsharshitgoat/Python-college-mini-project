"""Main dashboard screen."""

from __future__ import annotations

import datetime

import customtkinter as ctk

from ui.components.data_table import DataTable
from ui.components.notification import notify
from ui.components.stat_card import StatCard
from ui.screens.base import ScreenBase
from ui.theme import (
    ERROR, MUTED, NAVY, SUCCESS, TEXT, WARNING, button_style,
    card_style, font,
)


class DashboardScreen(ScreenBase):
    def __init__(self, master, ctx, nav, **kwargs):
        super().__init__(master, ctx, nav, "Dashboard", "Your event operations at a glance")
        self.session = ctx.session
        hour = datetime.datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        self.set_heading(
            f"{greeting}, {self.session.display_name.split()[0]}",
            "Here's what is happening across your events today.",
        )

        self.add_action("Open Scanner", self._open_scanner, "primary", 130)

        self.cards_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.cards_frame.pack(fill="x")
        for index in range(4):
            self.cards_frame.grid_columnconfigure(index, weight=1)

        self.metric_cards = []
        for index, (label, icon, color) in enumerate((
            ("Total Events", "▤", NAVY),
            ("Registrations", "✎", TEXT),
            ("Checked In", "✓", SUCCESS),
            ("Pending", "◷", WARNING),
        )):
            card = StatCard(
                self.cards_frame, label=label, value=0, icon=icon,
                accent=color, hint="",
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            self.metric_cards.append(card)

        actions = ctk.CTkFrame(self.body, **card_style())
        actions.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(
            actions, text="QUICK ACTIONS", font=font(11, "bold"), text_color=MUTED,
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(14, 8))
        row = ctk.CTkFrame(actions, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 16))
        for text, command, kind in (
            ("＋ Create Event", self._new_event, "secondary"),
            ("＋ Register Person", self._open_registration, "primary"),
            ("▣ Open Scanner", self._open_scanner, "primary"),
            ("▤ Generate Report", self._reports, "outline"),
        ):
            ctk.CTkButton(
                row, text=text, height=38, font=font(12, "bold"),
                command=command, **button_style(kind),
            ).pack(side="left", padx=(6, 0))

        self.events_frame = ctk.CTkFrame(self.body, **card_style())
        self.events_frame.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(
            self.events_frame, text="RECENT EVENTS", font=font(12, "bold"),
            text_color=TEXT, anchor="w",
        ).pack(anchor="w", padx=18, pady=(14, 6))
        self.events_table = DataTable(
            self.events_frame,
            columns=[("Event", 3), ("Date", 2), ("Venue", 3), ("Registered", 2), ("Status", 2)],
            empty_text="No events yet. Create your first event to get started.",
        )
        self.events_table.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        self.checkins_frame = ctk.CTkFrame(self.body, **card_style())
        self.checkins_frame.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(
            self.checkins_frame, text="RECENT CHECK-INS", font=font(12, "bold"),
            text_color=TEXT, anchor="w",
        ).pack(anchor="w", padx=18, pady=(14, 6))
        self.checkins_table = DataTable(
            self.checkins_frame,
            columns=[("Participant", 3), ("Event", 3), ("Registration", 2), ("Time", 2)],
            empty_text="No check-ins recorded yet.",
        )
        self.checkins_table.pack(fill="both", expand=True, padx=10, pady=(0, 12))

    def refresh(self):
        from utils.date_utils import format_date, format_time

        metrics = self.ctx.report_controller.dashboard()
        for card, value, hint in zip(
            self.metric_cards,
            (
                metrics["total_events"],
                metrics["total_registrations"],
                metrics["total_checkins"],
                metrics["pending"],
            ),
            (
                "All time",
                "Active tickets",
                "Successful entries",
                f"{metrics['attendance_rate']}% attendance",
            ),
        ):
            card.set_value(value, hint=hint)

        events = self.ctx.report_controller.recent_events(5)
        self.events_table.set_rows(
            [
                (
                    event.event_name,
                    event.event_date,
                    event.venue,
                    event.registered_count,
                    event.status_label,
                )
                for event in events
            ]
        )

        checkins = self.ctx.report_controller.recent_checkins(5)
        self.checkins_table.set_rows(
            [
                (
                    item.full_name,
                    item.event_name,
                    item.registration_code,
                    format_time(item.checked_in_at),
                )
                for item in checkins
            ]
        )

    def _new_event(self):
        if self.ctx.session.can("events.manage"):
            self.nav.navigate("events", open_dialog=True)
        else:
            notify(self, "Your role cannot manage events.", "warning")

    def _open_registration(self):
        if self.ctx.session.can("registrations.manage"):
            self.nav.navigate("registration")
        else:
            notify(self, "Your role cannot register participants.", "warning")

    def _open_scanner(self):
        if self.ctx.session.can("scanner"):
            self.nav.navigate("scanner")
        else:
            notify(self, "Your role cannot operate the scanner.", "warning")

    def _reports(self):
        if self.ctx.session.can("reports.view"):
            self.nav.navigate("reports")
        else:
            notify(self, "Your role cannot view reports.", "warning")
