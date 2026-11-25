"""Attendance management screen."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.data_table import DataTable
from ui.components.dialogs import ConfirmDialog, MessageDialog, ModalDialog
from ui.components.helpers import debounced
from ui.components.notification import notify
from ui.components.stat_card import StatCard
from ui.screens.base import ScreenBase
from ui.theme import (
    MUTED, NAVY, SUCCESS, TEXT, WARNING, button_style, card_style, font,
)
from utils.date_utils import format_time


class ManualCheckinDialog(ModalDialog):
    def __init__(self, master, on_submit, initial_value: str = ""):
        super().__init__(master, "Manual Check-in", width=440, height=240)
        self.on_submit = on_submit
        frame = ctk.CTkFrame(self, **card_style())
        frame.pack(fill="both", expand=True, padx=22, pady=(22, 4))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame, text="Registration ID (e.g. REG-000001)",
            font=font(12, "bold"), text_color=TEXT, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))
        self.entry = ctk.CTkEntry(
            frame, height=38, font=font(13), placeholder_text="REG-000001"
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=18)
        if initial_value:
            self.entry.insert(0, initial_value)
        self.entry.bind("<Return>", lambda _event: self._submit())
        self.footer([
            ("Cancel", "outline", self.destroy),
            ("Mark Present", "primary", self._submit),
        ])

    def _submit(self) -> None:
        if self.on_submit(self.entry.get().strip()):
            self.destroy()


class AttendanceScreen(ScreenBase):
    def __init__(self, master, ctx, nav, event_id: int | None = None, **kwargs):
        super().__init__(master, ctx, nav, "Attendance", "Check-in records and participant status")
        self.initial_event_id = event_id
        self.event_ids: dict[str, int] = {}
        self._registrations: list = []
        self.selected_id: int | None = None
        self.search_var = ctk.StringVar()
        self.filter_var = ctk.StringVar(value="all")

        toolbar = ctk.CTkFrame(self.body, **card_style())
        toolbar.pack(fill="x")
        ctk.CTkLabel(
            toolbar, text="EVENT", font=font(10, "bold"), text_color=MUTED, anchor="w"
        ).pack(anchor="w", padx=14, pady=(12, 2))
        self.event_var = ctk.StringVar()
        self.event_combo = ctk.CTkComboBox(
            toolbar, values=["Loading..."], variable=self.event_var,
            state="readonly", height=36, font=font(12), width=280,
            command=lambda *_: self.refresh(),
        )
        self.event_combo.pack(side="left", padx=14, pady=(24, 14))

        self._on_search = debounced(self, self.refresh, 220)
        self.search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(
            toolbar, placeholder_text="Search participant...",
            textvariable=self.search_var, height=36, font=font(12), width=230,
        ).pack(side="left", padx=8, pady=(24, 14))
        ctk.CTkComboBox(
            toolbar, values=["all", "present", "pending", "cancelled"],
            variable=self.filter_var, state="readonly", height=36,
            font=font(12), width=130, command=lambda *_: self.refresh(),
        ).pack(side="left", padx=4, pady=(24, 14))
        export = ctk.CTkButton(
            toolbar, text="Export CSV", height=36, font=font(12, "bold"),
            command=self._export, **button_style("secondary"),
        )
        export.pack(side="right", padx=14, pady=(24, 14))
        if not ctx.session.can("reports.export"):
            export.configure(state="disabled")

        self.stats_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(14, 0))
        self.stat_cards = []
        for index, (label, color) in enumerate((
            ("Total Registered", NAVY), ("Present", SUCCESS), ("Pending", WARNING)
        )):
            card = StatCard(self.stats_frame, label, 0, accent=color)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            self.stats_frame.grid_columnconfigure(index, weight=1)
            self.stat_cards.append(card)

        self.table = DataTable(
            self.body,
            columns=[("Name", 3), ("Registration", 2), ("Phone", 2), ("Status", 2), ("Check-in", 2)],
            on_select=self._on_select,
            empty_text="No registrations found for this event.",
        )
        self.table.pack(fill="both", expand=True, pady=(14, 0))

        actions = ctk.CTkFrame(self.body, **card_style())
        actions.pack(fill="x", pady=(12, 0))
        self.manual_btn = ctk.CTkButton(
            actions, text="Mark Manually Present", height=34, font=font(12),
            command=self._manual, state="disabled", **button_style("outline"),
        )
        self.manual_btn.pack(side="left", padx=12, pady=12)
        if not ctx.session.can("attendance.manual"):
            self.manual_btn.configure(state="disabled")
        self.remove_btn = ctk.CTkButton(
            actions, text="Remove from Event", height=34, font=font(12),
            command=self._remove, state="disabled", **button_style("danger"),
        )
        self.remove_btn.pack(side="left", padx=(10, 0), pady=12)
        if not ctx.session.can("registrations.manage"):
            self.remove_btn.configure(state="disabled")
        ctk.CTkLabel(
            actions, text="Manual check-in requires administrator permission and is audit logged.",
            font=font(10), text_color=MUTED, anchor="w",
        ).pack(side="left", padx=10)

    def refresh(self):
        events = self.ctx.event_controller.list().data or []
        labels = [f"#{event.event_id}  {event.event_name}" for event in events]
        self.event_ids = dict(zip(labels, [event.event_id for event in events]))
        self.event_combo.configure(values=labels or ["No events"])
        if labels:
            preferred = next(
                (label for label, eid in self.event_ids.items()
                 if eid == getattr(self, "initial_event_id", None)),
                labels[0],
            )
            self.event_var.set(preferred)

        event_id = self.current_event_id()
        if not event_id:
            self.table.set_rows([])
            for card in self.stat_cards:
                card.set_value(0)
            return

        summary = self.ctx.attendance_controller.summary(event_id).data or {}
        for card, value in zip(
            self.stat_cards,
            (summary.get("total", 0), summary.get("present", 0), summary.get("pending", 0)),
        ):
            card.set_value(value)

        result = self.ctx.registration_controller.list_for_event(
            event_id, self.search_var.get().strip(), self.filter_var.get()
        )
        self._registrations = result.data or []
        self.table.set_rows(
            [
                (
                    item.full_name,
                    item.code,
                    item.phone,
                    "PRESENT" if item.is_present else item.registration_status,
                    format_time(item.checked_in_at) if item.checked_in_at else "-",
                )
                for item in self._registrations
            ]
        )
        self.selected_id = None
        if self.ctx.session.can("attendance.manual"):
            self.manual_btn.configure(state="disabled")
        self.remove_btn.configure(state="disabled")

    def current_event_id(self) -> int | None:
        return self.event_ids.get(self.event_var.get())

    def _on_select(self, index: int) -> None:
        if 0 <= index < len(self._registrations):
            self.selected_id = self._registrations[index].registration_id
            if self.ctx.session.can("attendance.manual"):
                self.manual_btn.configure(state="normal")
            if self.ctx.session.can("registrations.manage"):
                self.remove_btn.configure(state="normal")

    def _manual(self) -> None:
        def submit(text: str) -> bool:
            registration_id = self._parse_id(text)
            if not registration_id:
                MessageDialog(self, "Manual Check-in", "Enter a valid registration ID.", "error")
                return False
            result = self.ctx.attendance_controller.manual_checkin(
                registration_id, self.ctx.session.user_id
            )
            notify(self, result.message, "success" if result.success else "error")
            if result.success:
                self.nav.mark_dirty("dashboard")
                self.nav.mark_dirty("reports")
                event_id = self.current_event_id()
                if event_id:
                    self.nav.mark_dirty("event_details", event_id=event_id)
            self.refresh()
            return result.success

        selected_code = f"REG-{self.selected_id:06d}" if self.selected_id else ""
        ManualCheckinDialog(self, submit, initial_value=selected_code)

    def _remove(self) -> None:
        registration = next(
            (item for item in self._registrations
             if item.registration_id == self.selected_id),
            None,
        )
        if not registration:
            return
        event_id = self.current_event_id()
        event_label = self.event_var.get() or "this event"

        def proceed():
            result = self.ctx.registration_controller.remove(
                registration.registration_id, self.ctx.session.user_id
            )
            notify(self, result.message, "success" if result.success else "error")
            if not result.success:
                return
            self.nav.mark_dirty("dashboard")
            self.nav.mark_dirty("events")
            self.nav.mark_dirty("reports")
            self.nav.mark_dirty("scanner")
            if event_id:
                self.nav.mark_dirty("event_details", event_id=event_id)
            self.refresh()

        ConfirmDialog(
            self, "Remove from Event",
            f"Permanently remove {registration.full_name} from {event_label}? "
            "Their QR ticket and check-in record will be deleted. The participant "
            "record stays available and they can be registered again later.",
            proceed, confirm_text="Remove Participant", danger=True,
        )

    @staticmethod
    def _parse_id(text: str) -> int | None:
        digits = "".join(character for character in text if character.isdigit())
        return int(digits) if digits else None

    def _export(self) -> None:
        event_id = self.current_event_id()
        if not event_id:
            notify(self, "Select an event first.", "warning")
            return
        result = self.ctx.attendance_controller.export("attendance", event_id)
        notify(self, result.message, "success" if result.success else "error")
