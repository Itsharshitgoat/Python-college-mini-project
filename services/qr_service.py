"""QR token generation, hashing, image generation and ticket rendering."""

from __future__ import annotations

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

from config import Paths
from models.registration import Registration
from utils.date_utils import format_date, format_time
from utils.file_utils import safe_filename
from utils.security import generate_token, hash_token, make_payload, parse_payload

_HEADER = "#172554"
_TEAL = "#14B8A6"
_TEXT = "#1E293B"
_MUTED = "#64748B"
_BORDER = "#E2E8F0"


class QrService:
    def __init__(self, paths: Paths):
        self.paths = paths

    # --- token payload -------------------------------------------------
    def new_token(self) -> str:
        return generate_token()

    def hash(self, token: str) -> str:
        return hash_token(token)

    def payload(self, token: str) -> str:
        return make_payload(token)

    def parse(self, payload: str | None) -> str | None:
        return parse_payload(payload)

    # --- QR images -----------------------------------------------------
    def make_qr_image(self, payload: str, box_size: int = 10) -> Image.Image:
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=box_size,
            border=3,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        return qr.make_image(fill_color=_HEADER, back_color="white").convert("RGB")

    def save_ticket_qr(self, registration_id: int, event_id: int, payload: str) -> Path:
        image = self.make_qr_image(payload)
        filename = f"REG-{registration_id:06d}.png"
        path = self.paths.event_qr_dir(event_id) / filename
        image.save(path)
        return path

    # --- full ticket image ---------------------------------------------
    @staticmethod
    def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        candidates = (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "Arial.ttf",
        )
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def render_ticket(self, registration: Registration, payload: str) -> Image.Image:
        """Render a printable digital entry pass as a PIL image."""
        width, height = 760, 980
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        draw.rectangle([0, 0, width, 140], fill=_HEADER)
        draw.text((width // 2, 40), "EVENTRA", font=self._font(38, True),
                  fill="white", anchor="mt")
        draw.text((width // 2, 92), "OFFICIAL ENTRY PASS", font=self._font(18),
                  fill="#99CEFF", anchor="mt")

        draw.text((width // 2, 180), registration.event_name.upper(),
                  font=self._font(30, True), fill=_TEXT, anchor="mt")
        draw.text((width // 2, 225), registration.event_date,
                  font=self._font(17), fill=_MUTED, anchor="mt")

        qr = self.make_qr_image(payload, box_size=9)
        qr = qr.resize((430, 430), Image.Resampling.NEAREST)
        qr_x = (width - qr.width) // 2
        draw.rounded_rectangle(
            [qr_x - 16, 280, qr_x + qr.width + 16, 280 + qr.height + 16],
            radius=18, outline=_BORDER, width=3,
        )
        image.paste(qr, (qr_x, 296))

        y = 770
        draw.text((width // 2, y), registration.full_name.upper(),
                  font=self._font(28, True), fill=_TEXT, anchor="mt")
        draw.text((width // 2, y + 48), registration.code,
                  font=self._font(18, True), fill=_TEAL, anchor="mt")

        draw.line([60, y + 92, width - 60, y + 92], fill=_BORDER, width=2)
        details = (
            f"DATE      : {format_date(registration.event_date)}",
            f"VENUE     : {registration.venue}",
            f"REGISTERED: {format_date(registration.registered_at)}",
            "STATUS    : VALID - ONE ENTRY PER TICKET",
        )
        for index, line in enumerate(details):
            draw.text((80, y + 115 + index * 30), line,
                      font=self._font(16), fill=_MUTED)

        draw.rectangle([0, height - 44, width, height], fill=_HEADER)
        draw.text((width // 2, height - 30), "Present this QR code at the event entrance",
                  font=self._font(14), fill="#99CEFF", anchor="mm")
        return image

    def ticket_filename(self, registration: Registration) -> str:
        return safe_filename(f"ticket_{registration.code}_{registration.full_name}") + ".png"
