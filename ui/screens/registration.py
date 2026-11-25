"""Participant registration and participant directory."""

from __future__ import annotations

import customtkinter as ctk

from ui.components.data_table import DataTable
from ui.components.dialogs import MessageDialog
from ui.components.helpers import debounced
from ui.components.notification import notify
from ui.screens.base import ScreenBase
from ui.theme import MUTED, TEXT, button_style, card_style, font


FIELDS = (
    ("full_name", "Full Name *", "Participant's full name"),
    ("email", "Email Address", "name@example.com (optional)"),
    ("phone", "Phone Number *", "Contact number"),
    ("college", "College", "Institution (optional)"),
    ("department", "Department", "Academic department"),
    ("year", "Academic Year", "e.g. 2nd Year"),
)


class RegistrationScreen(ScreenBase):
    def __init__(self, master, ctx, nav, mode: str = "register", event_id: int | None = None, **kwargs):
        self.mode = mode
        if mode == "participants":
            super().__init__(master, ctx, nav, "Participants", "Participant directory and registration history")
            self._build_directory()
        else:
            super().__init__(master, ctx, nav, "New Registration", "Add a participant to an event")
            self.initial_event_id = event_id
            self._build_form()

    # --- registration form ---------------------------------------------
    def _build_form(self) -> None:
        self.event_ids: dict[str, int] = {}
        self.entries: dict[str, ctk.CTkEntry] = {}

        card = ctk.CTkFrame(self.body, **card_style())
        card.pack(fill="x")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="SELECT EVENT", font=font(11, "bold"), text_color=MUTED, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 4))
        self.event_var = ctk.StringVar()
        self.event_combo = ctk.CTkComboBox(
            card, values=["Loading events..."], variable=self.event_var,
            state="readonly", height=40, font=font(13),
        )
        self.event_combo.grid(row=1, column=0, sticky="ew", padx=22)

        section = ctk.CTkFrame(card, fg_color="transparent")
        section.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        section.grid_columnconfigure(0, weight=1)
        section.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            section, text="PARTICIPANT INFORMATION", font=font(11, "bold"),
            text_color=MUTED, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(4, 10))

        for index, (key, label, placeholder) in enumerate(FIELDS):
            row = 1 + index // 2
            column = index % 2
            ctk.CTkLabel(
                section, text=label, font=font(12, "bold"), text_color=TEXT, anchor="w"
            ).grid(row=row * 2 - 1, column=column, sticky="w", padx=22, pady=(8, 4))
            entry = ctk.CTkEntry(
                section, height=40, font=font(13), placeholder_text=placeholder
            )
            entry.grid(
                row=row * 2, column=column, sticky="ew", padx=22, pady=(0, 6)
            )
            self.entries[key] = entry

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", pady=(10, 22))
        ctk.CTkButton(
            buttons, text="Cancel", height=40, width=120, font=font(12, "bold"),
            command=self._clear, **button_style("outline"),
        ).pack(side="right", padx=(10, 22))
        register = ctk.CTkButton(
            buttons, text="Register Participant", height=40, width=200,
            font=font(12, "bold"), command=self._submit_registration, **button_style("primary"),
        )
        register.pack(side="right")
        if not self.ctx.session.can("registrations.manage"):
            register.configure(state="disabled")

    def refresh(self):
        if self.mode == "participants":
            self._refresh_directory()
            return
        events = [
            event for event in (self.ctx.event_controller.list().data or [])
            if event.registration_status == "OPEN"
        ]
        labels = [
            f"#{event.event_id}  {event.event_name}  ({event.registered_count}/{event.capacity})"
            for event in events
        ]
        self.event_ids = {
            label: event.event_id for label, event in zip(labels, events)
        }
        self.event_combo.configure(values=labels or ["No open events"])
        if labels:
            preferred = next(
                (label for label, event_id in self.event_ids.items()
                 if event_id == getattr(self, "initial_event_id", None)),
                labels[0],
            )
            self.event_var.set(preferred)
        else:
            self.event_var.set("No open events")

    def _clear(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")

    def _submit_registration(self) -> None:
        event_id = self.event_ids.get(self.event_var.get())
        if not event_id:
            MessageDialog(self, "Registration", "Select an open event first.", "error")
            return
        form = {
            "event_id": event_id,
            **{key: entry.get().strip() for key, entry in self.entries.items()},
        }
        result = self.ctx.registration_controller.register(
            form, self.ctx.session.user_id
        )
        if not result.success:
            MessageDialog(self, "Registration failed", result.message, "error")
            return
        notify(self, result.message, "success")
        from ui.screens.ticket_preview import TicketDialog

        TicketDialog(
            self, result.data["registration"], result.data["payload"], self.ctx
        )
        self.nav.mark_dirty("dashboard")
        self.nav.mark_dirty("events")
        self.nav.mark_dirty("event_details", event_id=event_id)
        self.nav.mark_dirty("attendance")
        self.nav.mark_dirty("reports")
        self._clear()
        self.refresh()

    # --- participant directory -----------------------------------------
    def _build_directory(self) -> None:
        toolbar = ctk.CTkFrame(self.body, **card_style())
        toolbar.pack(fill="x")
        self.search_var = ctk.StringVar()
        self._on_search = debounced(self, self._refresh_directory, 220)
        self.search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(
            toolbar, placeholder_text="Search name, phone, email or college...",
            textvariable=self.search_var, height=38, font=font(13), width=380,
        ).pack(side="left", padx=14, pady=14)

        self.table = DataTable(
            self.body,
            columns=[("Name", 3), ("Phone", 2), ("Email", 3), ("College", 3), ("Events", 2)],
            empty_text="No participants found.",
        )
        self.table.pack(fill="both", expand=True, pady=(14, 0))

    def _refresh_directory(self) -> None:
        result = self.ctx.participant_controller.search(self.search_var.get())
        participants = result.data or []
        rows = []
        for participant in participants:
            history = self.ctx.registration_controller.list_for_participant(
                participant.participant_id
            ).data or []
            rows.append(
                (
                    participant.full_name,
                    participant.phone,
                    participant.email or "-",
                    participant.college or "-",
                    len(history),
                )
            )
        self.table.set_rows(rows)
