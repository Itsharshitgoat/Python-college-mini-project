"""Form and field validation helpers."""

from __future__ import annotations

from datetime import datetime
import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_ALLOWED_RE = re.compile(r"^\+?[0-9\s\-()]+$")


def validate_required(value, label: str) -> str | None:
    if value is None or not str(value).strip():
        return f"{label} is required."
    return None


def validate_date(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return "Event date is required."
    try:
        parts = text.split("-")
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            datetime(year, month, day)
            if 1900 <= year <= 2100:
                return None
    except (ValueError, TypeError):
        pass
    return "Event date must be a valid date in YYYY-MM-DD format."


def validate_email(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None  # email is optional
    return None if EMAIL_RE.match(value) else "Enter a valid email address."


def validate_phone(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return "Phone number is required."
    if not PHONE_ALLOWED_RE.match(value):
        return "Phone number contains invalid characters."
    digits = re.sub(r"[^0-9]", "", value)
    if not 7 <= len(digits) <= 15:
        return "Enter a valid phone number (7-15 digits)."
    return None


def validate_capacity(value) -> str | None:
    try:
        capacity = int(str(value).strip())
    except (ValueError, TypeError):
        return "Capacity must be a whole number."
    return None if 1 <= capacity <= 100000 else "Capacity must be between 1 and 100000."


def validate_event_form(data: dict) -> str | None:
    for field, label in (
        ("event_name", "Event name"),
        ("venue", "Venue"),
    ):
        error = validate_required(data.get(field), label)
        if error:
            return error
    date_error = validate_date(data.get("event_date"))
    if date_error:
        return date_error
    return validate_capacity(data.get("capacity"))


def validate_participant_form(data: dict) -> str | None:
    for field, label in (("full_name", "Full name"), ("phone", "Phone number")):
        error = validate_required(data.get(field), label)
        if error:
            return error
    error = validate_phone(data.get("phone"))
    if error:
        return error
    return validate_email(data.get("email"))
