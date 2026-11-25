"""Event management screen."""

from __future__ import annotations

import customtkinter as ctk

from config import EVENT_STATUSES
from ui.components.data_table import DataTable
from ui.components.dialogs import ConfirmDialog, EventDialog, MessageDialog
from ui.components.helpers import debounced
from ui.components.notification import notify
from ui.screens.base import ScreenBase
from ui.theme import button_style, card_style, font


class EventsScreen(ScreenBase):
    def __init__(self, master, ctx, nav, **kwargs):
        super().__init__(master, ctx, nav, "Events", "Create and manage your organization's events")
        self.selected_event_id: int | None = None
        self._events: list = []
        self.search_var = ctk.StringVar()
        self.status_var = ctk.StringVar(value="All Events")
        self.can_manage = ctx.session.can("events.manage")
        self.can_register = ctx.session.can("registrations.manage")

        toolbar = ctk.CTkFrame(self.body, **card_style())
        toolbar.pack(fill="x")
        self._on_search = debounced(self, self.refresh, 220)
        self.search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(
            toolbar, placeholder_text="Search events or venues...",
            textvariable=self.search_var, height=38, font=font(13), width=300,
        ).pack(side="left", padx=(14, 8), pady=14)
        ctk.CTkComboBox(
            toolbar, values=["All Events", *EVENT_STATUSES],
            variable=self.status_var, state="readonly", height=38, font=font(12),
            width=160, command=lambda *_: self.refresh(),
        ).pack(side="left", padx=4, pady=14)
        if self.can_manage:
            ctk.CTkButton(
                toolbar, text="＋ New Event", height=38, font=font(12, "bold"),
                command=self._create, **button_style("primary"),
            ).pack(side="right", padx=14, pady=14)

        self.table = DataTable(
            self.body,
            columns=[
                ("Event", 4), ("Date", 2), ("Venue", 3),
                ("Registered", 2), ("Reg. Status", 2), ("Check-in", 2),
            ],
            on_select=self._on_select,
            on_double_click=self._on_double_click,
            empty_text="No events found. Create a new event to begin.",
        )
        self.table.pack(fill="both", expand=True, pady=(14, 0))

        actions = ctk.CTkFrame(self.body, **card_style())
        actions.pack(fill="x", pady=(12, 0))
        for column in range(3):
            actions.grid_columnconfigure(column, weight=1)

        self.action_buttons = {}
        specs = (
            ("view", "Open Event", "secondary", self._view, True),
            ("register", "Register Person", "primary", self._register_person, self.can_register),
            ("edit", "Edit Event", "outline", self._edit, self.can_manage),
            ("registration", "Toggle Registration", "outline", self._toggle_registration, self.can_manage),
            ("checkin", "Toggle Check-in", "outline", self._toggle_checkin, self.can_manage),
            ("delete", "Delete Event", "danger", self._delete, self.can_manage),
        )
        for index, (key, text, kind, command, allowed) in enumerate(specs):
            button = ctk.CTkButton(
                actions, text=text, height=34, font=font(11, "bold"),
                command=command, **button_style(kind), state="disabled",
            )
            button.grid(
                row=index // 3, column=index % 3, sticky="ew",
                padx=(10, 0), pady=(10, 0) if index < 3 else (6, 12),
            )
            self.action_buttons[key] = (button, allowed)
        self._set_actions_state()

    def refresh(self):
        result = self.ctx.event_controller.list(
            self.search_var.get().strip(), self.status_var.get()
        )
        self._events = result.data or []
        self.table.set_rows(
            [
                (
                    event.event_name,
                    event.event_date,
                    event.venue,
                    f"{event.registered_count}/{event.capacity}",
                    event.registration_status,
                    event.checkin_status,
                )
                for event in self._events
            ]
        )

        selected = self.selected_event_id
        match = next(
            (index for index, event in enumerate(self._events)
             if event.event_id == selected),
            None,
        )
        if match is None:
            self.selected_event_id = None
        else:
            self.table.select(match)
        self._set_actions_state()

    def _set_actions_state(self) -> None:
        has_selection = self.selected_event_id is not None
        for button, allowed in self.action_buttons.values():
            button.configure(state="normal" if has_selection and allowed else "disabled")

    def _on_select(self, index: int) -> None:
        if 0 <= index < len(self._events):
            self.selected_event_id = self._events[index].event_id
            self._set_actions_state()

    def _on_double_click(self, index: int) -> None:
        self._on_select(index)
        self._view()

    def _selected(self):
        if self.selected_event_id is None:
            return None
        return next(
            (event for event in self._events if event.event_id == self.selected_event_id),
            None,
        )

    def _mark_event_changed(self) -> None:
        self.nav.mark_dirty("dashboard")
        self.nav.mark_dirty("attendance")
        self.nav.mark_dirty("reports")

    def _save_event(self, form: dict, publish: bool) -> bool:
        result = self.ctx.event_controller.create(form, self.ctx.session.user_id)
        if not result.success:
            MessageDialog(self, "Could not create event", result.message, "error")
            return False
        notify(self, "Event created successfully.", "success")
        self.selected_event_id = result.data["event_id"]
        self._mark_event_changed()
        self.refresh()
        return True

    def _create(self):
        if self.can_manage:
            EventDialog(self, on_save=self._save_event)

    def _view(self):
        event = self._selected()
        if event:
            self.nav.navigate("event_details", event_id=event.event_id)

    def _register_person(self):
        event = self._selected()
        if event:
            self.nav.navigate(
                "event_details", event_id=event.event_id, open_registration=True
            )

    def _edit(self):
        event = self._selected()
        if not event:
            return

        def save(form: dict, _publish: bool) -> bool:
            result = self.ctx.event_controller.update(
                event.event_id, form, self.ctx.session.user_id
            )
            if not result.success:
                MessageDialog(self, "Could not update event", result.message, "error")
                return False
            notify(self, "Event updated.", "success")
            self.nav.invalidate("event_details", event_id=event.event_id)
            self.nav.mark_dirty("event_details", event_id=event.event_id)
            self._mark_event_changed()
            self.refresh()
            return True

        EventDialog(self, on_save=save, event=event)

    def _toggle_registration(self):
        event = self._selected()
        if not event:
            return
        new_value = "CLOSED" if event.registration_status == "OPEN" else "OPEN"
        result = self.ctx.event_controller.set_status(
            event.event_id, "registration_status", new_value, self.ctx.session.user_id
        )
        notify(self, result.message, "success" if result.success else "error")
        if result.success:
            self.nav.mark_dirty("event_details", event_id=event.event_id)
            self._mark_event_changed()
        self.refresh()

    def _toggle_checkin(self):
        event = self._selected()
        if not event:
            return
        new_value = "CLOSED" if event.checkin_status == "OPEN" else "OPEN"
        result = self.ctx.event_controller.set_status(
            event.event_id, "checkin_status", new_value, self.ctx.session.user_id
        )
        notify(self, result.message, "success" if result.success else "error")
        if result.success:
            self.nav.mark_dirty("event_details", event_id=event.event_id)
            self._mark_event_changed()
        self.refresh()

    def _delete(self):
        event = self._selected()
        if not event:
            return

        def confirm():
            result = self.ctx.event_controller.delete(
                event.event_id, self.ctx.session.user_id
            )
            notify(self, result.message, "success" if result.success else "error")
            if result.success:
                self.nav.invalidate("event_details", event_id=event.event_id)
                self.nav.mark_dirty("dashboard")
                self.nav.mark_dirty("attendance")
                self.nav.mark_dirty("reports")
                self.nav.mark_dirty("scanner")
                self.selected_event_id = None
            self.refresh()

        ConfirmDialog(
            self, "Delete Event",
            f"Delete '{event.event_name}' and all of its registrations and attendance records? "
            "This cannot be undone.",
            confirm, confirm_text="Delete Event", danger=True,
        )
