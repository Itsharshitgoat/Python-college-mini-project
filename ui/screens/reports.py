"""Analytics and report exports."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.bar_chart import BarChart
from ui.components.notification import notify
from ui.components.stat_card import StatCard
from ui.screens.base import ScreenBase
from ui.theme import (
    MUTED, NAVY, SUCCESS, WARNING, button_style, card_style, font,
)


class ReportsScreen(ScreenBase):
    def __init__(self, master, ctx, nav, **kwargs):
        super().__init__(master, ctx, nav, "Analytics & Reports", "Attendance insights and CSV exports")
        self.event_ids: dict[str, int | None] = {}
        self.can_export = ctx.session.can("reports.export")

        self.stats_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.stats_frame.pack(fill="x")
        for index in range(4):
            self.stats_frame.grid_columnconfigure(index, weight=1)

        self.metric_cards = []
        for index, label in enumerate(("Registrations", "Checked In", "Pending", "Attendance Rate")):
            card = StatCard(self.stats_frame, label, 0)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            self.metric_cards.append(card)

        self.charts = ctk.CTkFrame(self.body, fg_color="transparent")
        self.charts.pack(fill="both", expand=True, pady=(16, 0))
        self.charts.grid_columnconfigure(0, weight=1)
        self.charts.grid_columnconfigure(1, weight=1)
        self.charts.grid_rowconfigure(0, weight=1)
        self.attendance_chart = BarChart(self.charts, "ATTENDANCE VS PENDING")
        self.attendance_chart.grid(row=0, column=0, sticky="nsew")
        self.hourly_chart = BarChart(self.charts, "CHECK-INS BY HOUR")
        self.hourly_chart.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        exports = ctk.CTkFrame(self.body, **card_style())
        exports.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(
            exports, text="EXPORT REPORTS", font=font(11, "bold"),
            text_color=MUTED, anchor="w",
        ).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(
            exports, text="Choose an event for event-specific reports, or leave blank for all events.",
            font=font(10), text_color=MUTED, anchor="w",
        ).pack(anchor="w", padx=18)
        controls = ctk.CTkFrame(exports, fg_color="transparent")
        controls.pack(fill="x", padx=14, pady=(10, 16))
        self.event_var = ctk.StringVar()
        self.event_combo = ctk.CTkComboBox(
            controls, values=["Loading..."], variable=self.event_var,
            state="readonly", height=36, font=font(12), width=300,
        )
        self.event_combo.pack(side="left", padx=4)
        for text, kind in (
            ("Attendance CSV", "primary"),
            ("Pending List", "outline"),
            ("Participant List", "outline"),
            ("Event Summary", "secondary"),
        ):
            ctk.CTkButton(
                controls, text=text, height=36, font=font(11, "bold"),
                command=lambda t=text: self._export(t), **button_style(kind),
            ).pack(side="left", padx=(6, 0))
        if not self.can_export:
            for child in controls.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(state="disabled")

    def refresh(self):
        metrics = self.ctx.report_controller.dashboard()
        values = (
            metrics["total_registrations"],
            metrics["total_checkins"],
            metrics["pending"],
            f"{metrics['attendance_rate']}%",
        )
        colors = (NAVY, SUCCESS, WARNING, SUCCESS)
        for card, value, color in zip(self.metric_cards, values, colors):
            card.set_value(value, accent=color)

        events = self.ctx.event_controller.list().data or []
        labels = ["All Events"] + [f"#{e.event_id}  {e.event_name}" for e in events]
        self.event_ids = {"All Events": None}
        self.event_ids.update(
            {label: event.event_id for label, event in zip(labels[1:], events)}
        )
        self.event_combo.configure(values=labels)
        if self.event_var.get() not in labels:
            self.event_var.set("All Events")

        self.attendance_chart.set_values(
            [("Checked In", metrics["total_checkins"]), ("Pending", metrics["pending"])],
            colors=("#14B8A6", "#D97706"),
        )
        by_hour = self.ctx.report_controller.checkin_by_hour() or []
        self.hourly_chart.set_values(
            [(self._hour_label(item[0]), item[1]) for item in by_hour],
            colors=("#172554",),
        )

    @staticmethod
    def _hour_label(hour) -> str:
        try:
            return f"{int(hour):02d}:00"
        except (TypeError, ValueError):
            return str(hour)

    def _export(self, label: str) -> None:
        kind = {
            "Attendance CSV": "attendance",
            "Pending List": "pending",
            "Participant List": "participants",
            "Event Summary": "event_summary",
        }[label]
        event_id = self.event_ids.get(self.event_var.get())
        result = self.ctx.report_controller.export(kind, event_id)
        notify(self, result.message, "success" if result.success else "error")
