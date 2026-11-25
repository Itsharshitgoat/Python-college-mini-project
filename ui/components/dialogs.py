"""Modal dialogs for forms and confirmations."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config import CHECKIN_STATUSES, EVENT_STATUSES, ROLES, ROLE_LABELS
from ui.theme import (
    BORDER, ERROR, MUTED, NAVY, SURFACE, TEXT, button_style, card_style, font,
)


class ModalDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, width: int = 560, height: int = 640):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color="#F5F7FA")
        self.geometry(f"{width}x{height}")
        self._center(master, width, height)
        self.after(120, self.grab_set)
        self.lift()

    def _center(self, master, width: int, height: int) -> None:
        try:
            x = master.winfo_rootx() + max(master.winfo_width() - width, 0) // 2
            y = master.winfo_rooty() + max(master.winfo_height() - height, 0) // 2
            self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
        except Exception:
            pass

    def footer(self, buttons: list[tuple[str, str, Callable]]) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=24, pady=(8, 20))
        for text, kind, command in buttons:
            ctk.CTkButton(
                frame, text=text, height=38, font=font(12, "bold"),
                command=command, **button_style(kind),
            ).pack(side="right", padx=(8, 0))
        return frame


class EventDialog(ModalDialog):
    """Create or edit an event."""

    def __init__(self, master, on_save: Callable[[dict, bool], bool], event=None):
        super().__init__(
            master,
            "New Event" if event is None else "Edit Event",
            width=620,
            height=760,
        )
        self.on_save = on_save
        self.event = event

        scroller = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroller.pack(fill="both", expand=True, padx=24, pady=(22, 4))
        scroller.grid_columnconfigure(0, weight=1)
        scroller.grid_columnconfigure(1, weight=1)

        self.entries: dict[str, ctk.CTkEntry] = {}
        row = 0

        def field(label: str, key: str, placeholder: str = "", span: bool = False,
                  required: bool = False):
            nonlocal row
            ctk.CTkLabel(
                scroller, text=label + (" *" if required else ""),
                font=font(12, "bold"), text_color=TEXT, anchor="w",
            ).grid(row=row, column=0, columnspan=2 if span else 1, sticky="w", pady=(12, 4))
            row += 1
            entry = ctk.CTkEntry(
                scroller, height=38, font=font(13), placeholder_text=placeholder
            )
            entry.grid(
                row=row, column=0, columnspan=2 if span else 1, sticky="ew", pady=(0, 4)
            )
            self.entries[key] = entry
            row += 1

        def combo(label: str, key: str, values, value: str):
            nonlocal row
            ctk.CTkLabel(
                scroller, text=label, font=font(12, "bold"), text_color=TEXT, anchor="w"
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 4))
            row += 1
            variable = ctk.StringVar(value=value)
            widget = ctk.CTkComboBox(
                scroller, values=list(values), variable=variable,
                state="readonly", height=36, font=font(12),
            )
            widget.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4))
            self.entries[key] = widget
            row += 1

        field("Event Name", "event_name", "e.g. TechFest 2026", required=True)
        ctk.CTkLabel(
            scroller, text="Description", font=font(12, "bold"), text_color=TEXT, anchor="w"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 4))
        row += 1
        self.description = ctk.CTkTextbox(scroller, height=80, font=font(12))
        self.description.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        row += 1

        ctk.CTkLabel(
            scroller, text="Event Date *  |  Maximum Capacity *",
            font=font(12, "bold"), text_color=TEXT, anchor="w",
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 4))
        row += 1

        # Place date and capacity side by side.
        date_entry = ctk.CTkEntry(
            scroller, height=38, font=font(13), placeholder_text="YYYY-MM-DD"
        )
        date_entry.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        self.entries["event_date"] = date_entry
        cap_entry = ctk.CTkEntry(
            scroller, height=38, font=font(13), placeholder_text="Maximum capacity"
        )
        cap_entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(0, 4))
        self.entries["capacity"] = cap_entry
        row += 1

        start = ctk.CTkEntry(scroller, height=38, font=font(13), placeholder_text="Start (HH:MM)")
        start.grid(row=row, column=0, sticky="ew", pady=(4, 4))
        self.entries["start_time"] = start
        end = ctk.CTkEntry(scroller, height=38, font=font(13), placeholder_text="End (HH:MM)")
        end.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(4, 4))
        self.entries["end_time"] = end
        row += 1

        field("Venue", "venue", "Event location", required=True)
        combo("Registration Status", "registration_status", EVENT_STATUSES, "DRAFT")
        combo("Check-in Status", "checkin_status", CHECKIN_STATUSES, "OPEN")

        if event:
            values = {
                "event_name": event.event_name,
                "event_date": event.event_date,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "venue": event.venue,
                "capacity": str(event.capacity),
                "registration_status": event.registration_status,
                "checkin_status": event.checkin_status,
            }
            for key, value in values.items():
                widget = self.entries[key]
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(value)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, value)
            self.description.delete("1.0", "end")
            self.description.insert("1.0", event.description)

        if event:
            self.footer(
                [
                    ("Cancel", "outline", self.destroy),
                    ("Save Changes", "primary", lambda: self._save(publish=False)),
                ]
            )
        else:
            self.footer(
                [
                    ("Cancel", "outline", self.destroy),
                    ("Publish Event", "primary", lambda: self._save(publish=True)),
                    ("Save Draft", "secondary", lambda: self._save(publish=False)),
                ]
            )

    def _save(self, publish: bool) -> None:
        form = {
            "event_name": self.entries["event_name"].get().strip(),
            "description": self.description.get("1.0", "end").strip(),
            "event_date": self.entries["event_date"].get().strip()[:10],
            "start_time": self.entries["start_time"].get().strip(),
            "end_time": self.entries["end_time"].get().strip(),
            "venue": self.entries["venue"].get().strip(),
            "capacity": self.entries["capacity"].get().strip(),
            "registration_status": (
                "OPEN" if publish else self.entries["registration_status"].get()
            ),
            "checkin_status": (
                "OPEN" if publish else self.entries["checkin_status"].get()
            ),
        }
        if self.on_save(form, publish):
            self.destroy()


class ParticipantDialog(ModalDialog):
    """Register a participant directly from an event's detail page."""

    FIELDS = (
        ("full_name", "Full Name", "Participant's full name", "*"),
        ("phone", "Phone Number", "Contact number", "*"),
        ("email", "Email Address", "name@example.com (optional)", ""),
        ("college", "College", "Institution (optional)", ""),
        ("department", "Department", "Academic department", ""),
        ("year", "Academic Year", "e.g. 2nd Year", ""),
    )

    def __init__(self, master, event, on_save: Callable[[dict], bool]):
        super().__init__(
            master, f"Register for {event.event_name}", width=580, height=620
        )
        self.on_save = on_save
        self.entries: dict[str, ctk.CTkEntry] = {}

        card = ctk.CTkFrame(self, **card_style())
        card.pack(fill="both", expand=True, padx=22, pady=(22, 4))
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text=f"Event: {event.event_name}  •  {event.registered_count}/{event.capacity} registered",
            font=font(11, "bold"), text_color=MUTED, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 10))

        for index, (key, label, placeholder, required) in enumerate(self.FIELDS):
            row = 1 + index // 2
            column = index % 2
            ctk.CTkLabel(
                card, text=f"{label}{required}", font=font(12, "bold"),
                text_color=TEXT, anchor="w",
            ).grid(row=row * 2, column=column, sticky="w", padx=18, pady=(8, 4))
            entry = ctk.CTkEntry(
                card, height=38, font=font(13), placeholder_text=placeholder
            )
            entry.grid(
                row=row * 2 + 1, column=column, sticky="ew", padx=18, pady=(0, 4)
            )
            self.entries[key] = entry

        self.entries["full_name"].focus_set()
        self.footer([
            ("Cancel", "outline", self.destroy),
            ("Register & Issue Ticket", "primary", self._save),
        ])

    def _save(self) -> None:
        form = {
            key: self.entries[key].get().strip() for key, *_ in self.FIELDS
        }
        if self.on_save(form):
            self.destroy()


class ConfirmDialog(ModalDialog):
    def __init__(self, master, title: str, message: str, on_confirm: Callable[[], None],
                 confirm_text: str = "Confirm", danger: bool = False):
        super().__init__(master, title, width=440, height=230)
        frame = ctk.CTkFrame(self, **card_style())
        frame.pack(fill="both", expand=True, padx=24, pady=(24, 4))
        ctk.CTkLabel(
            frame, text=message, font=font(13), text_color=TEXT,
            wraplength=360, justify="left", anchor="w",
        ).pack(fill="x", padx=20, pady=24)
        self.footer(
            [
                ("Cancel", "outline", self.destroy),
                (confirm_text, "danger" if danger else "primary", self._confirm),
            ]
        )
        self._on_confirm = on_confirm

    def _confirm(self) -> None:
        self.destroy()
        self._on_confirm()


class MessageDialog(ModalDialog):
    def __init__(self, master, title: str, message: str, kind: str = "info"):
        super().__init__(master, title, width=440, height=220)
        frame = ctk.CTkFrame(self, **card_style())
        frame.pack(fill="both", expand=True, padx=24, pady=(24, 4))
        color = ERROR if kind == "error" else NAVY
        ctk.CTkLabel(
            frame, text=message, font=font(13), text_color=color,
            wraplength=360, justify="left", anchor="w",
        ).pack(fill="x", padx=20, pady=26)
        self.footer([("OK", "primary", self.destroy)])


class CreateUserDialog(ModalDialog):
    def __init__(self, master, on_save: Callable[[dict], bool]):
        super().__init__(master, "New User Account", width=480, height=500)
        self.on_save = on_save
        frame = ctk.CTkFrame(self, **card_style())
        frame.pack(fill="both", expand=True, padx=24, pady=(24, 4))
        frame.grid_columnconfigure(0, weight=1)
        self.entries: dict[str, ctk.CTkEntry] = {}

        for row, (label, key, placeholder, show) in enumerate((
            ("Username", "username", "Login username", None),
            ("Full Name", "full_name", "Optional display name", None),
            ("Password", "password", "At least 6 characters", "*"),
        )):
            ctk.CTkLabel(
                frame, text=label, font=font(12, "bold"), text_color=TEXT, anchor="w"
            ).grid(row=row * 2, column=0, sticky="w", padx=20, pady=(14, 4))
            entry = ctk.CTkEntry(
                frame, height=38, font=font(13), placeholder_text=placeholder, show=show or ""
            )
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", padx=20)
            self.entries[key] = entry

        ctk.CTkLabel(
            frame, text="Role", font=font(12, "bold"), text_color=TEXT, anchor="w"
        ).grid(row=6, column=0, sticky="w", padx=20, pady=(14, 4))
        self.role_var = ctk.StringVar(value=ROLES[1])
        ctk.CTkComboBox(
            frame, values=[ROLE_LABELS[role] for role in ROLES],
            variable=self.role_var, state="readonly", height=36, font=font(12),
        ).grid(row=7, column=0, sticky="ew", padx=20)

        self.footer(
            [
                ("Cancel", "outline", self.destroy),
                ("Create User", "primary", self._save),
            ]
        )

    def _save(self) -> None:
        role_label = self.role_var.get()
        role = next((r for r in ROLES if ROLE_LABELS[r] == role_label), ROLES[1])
        form = {
            "username": self.entries["username"].get().strip(),
            "full_name": self.entries["full_name"].get().strip(),
            "password": self.entries["password"].get(),
            "role": role,
        }
        if self.on_save(form):
            self.destroy()


class ChangePasswordDialog(ModalDialog):
    def __init__(self, master, on_save: Callable[[str, str, str], bool]):
        super().__init__(master, "Change Password", width=460, height=440)
        self.on_save = on_save
        frame = ctk.CTkFrame(self, **card_style())
        frame.pack(fill="both", expand=True, padx=24, pady=(24, 4))
        frame.grid_columnconfigure(0, weight=1)
        self.entries: dict[str, ctk.CTkEntry] = {}
        for row, (label, key) in enumerate((
            ("Current Password", "current"),
            ("New Password", "new"),
            ("Confirm New Password", "confirm"),
        )):
            ctk.CTkLabel(
                frame, text=label, font=font(12, "bold"), text_color=TEXT, anchor="w"
            ).grid(row=row * 2, column=0, sticky="w", padx=20, pady=(14, 4))
            entry = ctk.CTkEntry(frame, height=38, font=font(13), show="*")
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", padx=20)
            self.entries[key] = entry
        self.footer(
            [
                ("Cancel", "outline", self.destroy),
                ("Update Password", "primary", self._save),
            ]
        )

    def _save(self) -> None:
        current = self.entries["current"].get()
        new = self.entries["new"].get()
        confirm = self.entries["confirm"].get()
        if self.on_save(current, new, confirm):
            self.destroy()
