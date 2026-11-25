"""Single-event overview and management."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.data_table import DataTable
from ui.components.dialogs import ConfirmDialog, MessageDialog, ParticipantDialog
from ui.components.notification import notify
from ui.components.stat_card import StatCard
from ui.screens.base import ScreenBase
from ui.theme import (
    MUTED, NAVY, SUCCESS, TEXT, WARNING, button_style, card_style, font,
)
from utils.date_utils import format_date, format_time


class EventDetailsScreen(ScreenBase):
    def __init__(self, master, ctx, nav, event_id: int, **kwargs):
        super().__init__(master, ctx, nav, "Event Details", "Event overview and registrations")
        self.event_id = event_id
        self.event = None
        self._registrations: list = []
        self.selected_id: int | None = None

        self.add_action("← Events", lambda: nav.navigate("events"), "outline", 100)
        if ctx.session.can("registrations.manage"):
            self.add_action("＋ Register Person", self._open_registration, "primary", 150)
        if ctx.session.can("scanner"):
            self.add_action("▣ Open Scanner", self._scanner, "secondary", 130)
        if ctx.session.can("events.manage"):
            self.add_action("Delete Event", self._delete_event, "danger", 110)

        self.info_card = ctk.CTkFrame(self.body, **card_style())
        self.info_card.pack(fill="x")
        for column in range(3):
            self.info_card.grid_columnconfigure(column, weight=1, uniform="info")

        self.stats_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(14, 0))
        self.stat_cards = []
        for index, (label, color) in enumerate((
            ("Registered", NAVY), ("Checked In", SUCCESS), ("Pending", WARNING)
        )):
            card = StatCard(self.stats_frame, label, 0, accent=color)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            self.stats_frame.grid_columnconfigure(index, weight=1)
            self.stat_cards.append(card)

        self.reg_card = ctk.CTkFrame(self.body, **card_style())
        self.reg_card.pack(fill="both", expand=True, pady=(16, 0))
        ctk.CTkLabel(
            self.reg_card, text="REGISTRATIONS", font=font(12, "bold"),
            text_color=TEXT, anchor="w",
        ).pack(anchor="w", padx=16, pady=(14, 6))
        self.table = DataTable(
            self.reg_card,
            columns=[
                ("Name", 3), ("Registration", 2), ("Phone", 2),
                ("Status", 2), ("Check-in", 2),
            ],
            on_select=self._on_select,
            empty_text="No registrations for this event yet.",
        )
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        actions = ctk.CTkFrame(self.body, **card_style())
        actions.pack(fill="x", pady=(12, 0))
        self.reissue_btn = ctk.CTkButton(
            actions, text="Reissue Ticket", height=34, font=font(12),
            command=self._reissue, state="disabled", **button_style("outline"),
        )
        self.cancel_btn = ctk.CTkButton(
            actions, text="Cancel Registration", height=34, font=font(12),
            command=self._cancel, state="disabled", **button_style("outline"),
        )
        self.remove_btn = ctk.CTkButton(
            actions, text="Remove from Event", height=34, font=font(12),
            command=self._remove, state="disabled", **button_style("danger"),
        )
        self.export_btn = ctk.CTkButton(
            actions, text="Export Attendance CSV", height=34, font=font(12),
            command=self._export, **button_style("secondary"),
        )
        for button in (self.reissue_btn, self.cancel_btn, self.remove_btn, self.export_btn):
            button.pack(side="left", padx=(10, 0), pady=12)
        if not ctx.session.can("tickets.view"):
            self.reissue_btn.configure(state="disabled")
        if not ctx.session.can("registrations.manage"):
            self.cancel_btn.configure(state="disabled")
            self.remove_btn.configure(state="disabled")
        if not ctx.session.can("reports.export"):
            self.export_btn.configure(state="disabled")

    def refresh(self):
        event_result = self.ctx.event_controller.get(self.event_id)
        if not event_result.success:
            notify(self, event_result.message, "error")
            self.nav.navigate("events")
            return
        event = self.event = event_result.data
        self.set_heading(event.event_name, f"{format_date(event.event_date)}  •  {event.venue}")

        for child in list(self.info_card.winfo_children()):
            child.destroy()
        details = [
            ("DATE", format_date(event.event_date)),
            ("TIME", f"{event.start_time or '-'} - {event.end_time or '-'}"),
            ("VENUE", event.venue),
            ("CAPACITY", str(event.capacity)),
            ("REGISTRATION", event.registration_status),
            ("CHECK-IN", event.checkin_status),
        ]
        for index, (label, value) in enumerate(details):
            column = index % 3
            row = index // 3
            cell = ctk.CTkFrame(self.info_card, fg_color="#F8FAFC", corner_radius=8)
            cell.grid(
                row=row, column=column, sticky="ew", padx=(14, 0),
                pady=(12, 0) if row == 0 else (8, 14),
            )
            ctk.CTkLabel(
                cell, text=label, font=font(10, "bold"), text_color=MUTED, anchor="w"
            ).pack(anchor="w", padx=12, pady=(10, 0))
            ctk.CTkLabel(
                cell, text=str(value), font=font(13, "bold"), text_color=TEXT, anchor="w"
            ).pack(anchor="w", padx=12, pady=(2, 10))
        if event.description:
            ctk.CTkLabel(
                self.info_card, text=event.description, font=font(12),
                text_color=MUTED, anchor="w", wraplength=900, justify="left",
            ).grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=(4, 14))

        for card, value in zip(
            self.stat_cards,
            (event.registered_count, event.attended_count, event.pending_count),
        ):
            card.set_value(value)

        result = self.ctx.registration_controller.list_for_event(self.event_id)
        self._registrations = result.data or []
        self.table.set_rows(
            [
                (
                    item.full_name,
                    item.code,
                    item.phone,
                    item.registration_status,
                    format_time(item.checked_in_at) if item.checked_in_at else "PENDING",
                )
                for item in self._registrations
            ]
        )
        self.selected_id = None
        self.reissue_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.remove_btn.configure(state="disabled")

    def _on_select(self, index: int) -> None:
        if 0 <= index < len(self._registrations):
            self.selected_id = self._registrations[index].registration_id
            if self.ctx.session.can("tickets.view"):
                self.reissue_btn.configure(state="normal")
            if self.ctx.session.can("registrations.manage"):
                self.cancel_btn.configure(state="normal")
                self.remove_btn.configure(state="normal")

    def _selected(self):
        return next(
            (item for item in self._registrations if item.registration_id == self.selected_id),
            None,
        )

    def _mark_changed(self) -> None:
        self.nav.mark_dirty("dashboard")
        self.nav.mark_dirty("events")
        self.nav.mark_dirty("attendance")
        self.nav.mark_dirty("reports")

    def _scanner(self):
        self.nav.navigate("scanner", event_id=self.event_id)

    def _open_registration(self):
        event_result = self.ctx.event_controller.get(self.event_id)
        if not event_result.success:
            MessageDialog(self, "Event unavailable", event_result.message, "error")
            return
        event = event_result.data
        if event.registration_status != "OPEN":
            notify(self, "Set event registration to OPEN before registering people.", "warning")
            return

        def save(form: dict) -> bool:
            payload = {"event_id": self.event_id, **form}
            result = self.ctx.registration_controller.register(
                payload, self.ctx.session.user_id
            )
            if not result.success:
                MessageDialog(self, "Registration failed", result.message, "error")
                return False
            notify(self, result.message, "success")
            from ui.screens.ticket_preview import TicketDialog

            TicketDialog(
                self, result.data["registration"], result.data["payload"], self.ctx
            )
            self._mark_changed()
            self.nav.mark_dirty("event_details", event_id=self.event_id)
            self.nav.refresh()
            return True

        ParticipantDialog(self, event, save)

    def _delete_event(self):
        if not self.event:
            self.refresh()
            return
        event_name = self.event.event_name

        def confirm():
            result = self.ctx.event_controller.delete(
                self.event_id, self.ctx.session.user_id
            )
            notify(self, result.message, "success" if result.success else "error")
            if not result.success:
                return
            self.nav.navigate("events")
            self.nav.invalidate("event_details", event_id=self.event_id)
            self.nav.mark_dirty("dashboard")
            self.nav.mark_dirty("attendance")
            self.nav.mark_dirty("reports")
            self.nav.mark_dirty("scanner")

        ConfirmDialog(
            self, "Delete Event",
            f"Delete '{event_name}' and all of its registrations and attendance records? "
            "This cannot be undone.",
            confirm, confirm_text="Delete Event", danger=True,
        )

    def _reissue(self):
        registration = self._selected()
        if not registration:
            return

        def proceed():
            result = self.ctx.registration_controller.reissue(
                registration.registration_id, self.ctx.session.user_id
            )
            if not result.success:
                MessageDialog(self, "Reissue failed", result.message, "error")
                return
            from ui.screens.ticket_preview import TicketDialog

            TicketDialog(self, result.data["registration"], result.data["payload"], self.ctx)
            self._mark_changed()
            self.refresh()

        ConfirmDialog(
            self, "Reissue Ticket",
            "This generates a new QR token and invalidates the current ticket. Continue?",
            proceed, confirm_text="Reissue Ticket",
        )

    def _cancel(self):
        registration = self._selected()
        if not registration:
            return

        def proceed():
            result = self.ctx.registration_controller.cancel(
                registration.registration_id, self.ctx.session.user_id
            )
            notify(self, result.message, "success" if result.success else "error")
            self._mark_changed()
            self.refresh()

        ConfirmDialog(
            self, "Cancel Registration",
            f"Cancel the registration for {registration.full_name}? Their ticket will no longer be valid.",
            proceed, confirm_text="Cancel Registration", danger=True,
        )

    def _remove(self):
        registration = self._selected()
        if not registration:
            return
        event_name = self.event.event_name if self.event else "this event"

        def proceed():
            result = self.ctx.registration_controller.remove(
                registration.registration_id, self.ctx.session.user_id
            )
            notify(self, result.message, "success" if result.success else "error")
            if not result.success:
                return
            self._mark_changed()
            self.nav.mark_dirty("event_details", event_id=self.event_id)
            self.nav.mark_dirty("scanner")
            self.refresh()

        ConfirmDialog(
            self, "Remove from Event",
            f"Permanently remove {registration.full_name} from '{event_name}'? "
            "Their QR ticket and check-in record will be deleted. The participant "
            "record stays available and they can be registered again later.",
            proceed, confirm_text="Remove Participant", danger=True,
        )

    def _export(self):
        result = self.ctx.attendance_controller.export("attendance", self.event_id)
        notify(self, result.message, "success" if result.success else "error")
        if result.success and self.ctx.session.can("settings.manage"):
            from ui.components.dialogs import MessageDialog as MD
            from utils.file_utils import open_path

            MD(self, "Report exported", f"Saved to:\n{result.data['path']}")
            open_path(result.data["path"].parent)
