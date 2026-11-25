"""Digital QR entry-pass preview dialog."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image
from tkinter import filedialog

from core.context import AppContext
from models.registration import Registration
from ui.components.dialogs import ModalDialog
from ui.components.notification import notify
from ui.theme import (
    BORDER, MUTED, NAVY, SURFACE, SUCCESS, TEXT, TEAL, button_style, card_style, font,
)
from utils.date_utils import format_date
from utils.file_utils import open_path


class TicketDialog(ModalDialog):
    def __init__(self, master, registration: Registration, payload: str, ctx: AppContext):
        super().__init__(master, "Entry Ticket", width=580, height=790)
        self.registration = registration
        self.payload = payload
        self.ctx = ctx
        self._last_path: Path | None = None

        card = ctk.CTkFrame(self, **card_style())
        card.pack(fill="both", expand=True, padx=22, pady=(22, 6))
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color=NAVY, corner_radius=12, height=96)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 0))
        ctk.CTkLabel(
            header, text="EVENTRA", font=font(24, "bold"), text_color="white"
        ).pack(pady=(16, 0))
        ctk.CTkLabel(
            header, text="OFFICIAL ENTRY PASS", font=font(11, "bold"),
            text_color="#99CEFF",
        ).pack()

        ctk.CTkLabel(
            card, text=registration.event_name.upper(), font=font(19, "bold"),
            text_color=TEXT, anchor="center",
        ).grid(row=1, column=0, sticky="ew", pady=(18, 0))
        ctk.CTkLabel(
            card, text=format_date(registration.event_date), font=font(12),
            text_color=MUTED, anchor="center",
        ).grid(row=2, column=0, sticky="ew")

        qr_image = ctx.ticket_controller.make_qr_image(payload, box_size=8).resize(
            (280, 280), Image.Resampling.NEAREST
        )
        self._qr = ctk.CTkImage(light_image=qr_image, dark_image=qr_image, size=(280, 280))
        qr_frame = ctk.CTkFrame(card, fg_color="white", corner_radius=14,
                                border_width=1, border_color=BORDER)
        qr_frame.grid(row=3, column=0, pady=(16, 10))
        ctk.CTkLabel(qr_frame, image=self._qr, text="").pack(padx=14, pady=14)

        ctk.CTkLabel(
            card, text=registration.full_name.upper(), font=font(17, "bold"),
            text_color=TEXT, anchor="center",
        ).grid(row=4, column=0, sticky="ew")
        ctk.CTkLabel(
            card, text=registration.code, font=font(13, "bold"),
            text_color=TEAL, anchor="center",
        ).grid(row=5, column=0, sticky="ew")

        details = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=10)
        details.grid(row=6, column=0, sticky="ew", padx=18, pady=(16, 0))
        details.grid_columnconfigure(0, weight=1)
        for index, (label, value) in enumerate((
            ("DATE", format_date(registration.event_date)),
            ("VENUE", registration.venue),
            ("REGISTERED", format_date(registration.registered_at)),
        )):
            ctk.CTkLabel(
                details, text=f"{label:<12}: {value}", font=font(11),
                text_color=TEXT, anchor="w",
            ).grid(row=index, column=0, sticky="w", padx=16, pady=(8, 0 if index < 2 else 10))

        status = ctk.CTkLabel(
            card, text="●  VALID  •  ONE ENTRY PER TICKET",
            font=font(11, "bold"), text_color=SUCCESS, anchor="center",
        )
        status.grid(row=7, column=0, sticky="ew", pady=(12, 0))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=8, column=0, sticky="ew", pady=(10, 16))
        ctk.CTkButton(
            buttons, text="Download Ticket", height=38, font=font(12, "bold"),
            command=self._download, **button_style("primary"),
        ).pack(side="left", padx=(18, 6))
        ctk.CTkButton(
            buttons, text="Print Ticket", height=38, font=font(12, "bold"),
            command=self._print, **button_style("outline"),
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            buttons, text="Close", height=38, font=font(12, "bold"),
            command=self.destroy, **button_style("secondary"),
        ).pack(side="left", padx=6)

    def _render(self):
        return self.ctx.ticket_controller.render_ticket(self.registration, self.payload)

    def _download(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Ticket",
            defaultextension=".png",
            initialfile=self.ctx.ticket_controller.filename(self.registration),
            filetypes=[("PNG Image", "*.png")],
        )
        if not path:
            return
        try:
            self._render().save(path)
            self._last_path = Path(path)
            notify(self, "Ticket downloaded successfully.", "success")
        except OSError as exc:
            notify(self, f"Could not save ticket: {exc}", "error")

    def _print(self) -> None:
        path = self.ctx.paths.exports_dir / self.ctx.ticket_controller.filename(
            self.registration
        )
        try:
            self._render().save(path)
            self._last_path = path
            open_path(path)
            notify(self, "Ticket opened for printing.", "success")
        except OSError as exc:
            notify(self, f"Could not print ticket: {exc}", "error")
