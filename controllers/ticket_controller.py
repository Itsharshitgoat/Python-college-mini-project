"""QR ticket rendering operations exposed to the UI."""

from __future__ import annotations

from PIL import Image

from models.registration import Registration
from services.qr_service import QrService


class TicketController:
    def __init__(self, service: QrService):
        self.service = service

    def make_qr_image(self, payload: str, box_size: int = 10) -> Image.Image:
        return self.service.make_qr_image(payload, box_size)

    def render_ticket(self, registration: Registration, payload: str) -> Image.Image:
        return self.service.render_ticket(registration, payload)

    def filename(self, registration: Registration) -> str:
        return self.service.ticket_filename(registration)
