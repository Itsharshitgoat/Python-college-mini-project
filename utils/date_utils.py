"""UTC storage and local display helpers for timestamps."""

from __future__ import annotations

from datetime import datetime, timezone

_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string ending in Z."""
    return utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")


def from_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def to_local(value: str | None) -> datetime | None:
    parsed = from_iso(value)
    return parsed.astimezone() if parsed else None


def format_date(value: str | None) -> str:
    if not value:
        return "-"
    text = str(value).strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        try:
            year, month, day = int(text[:4]), int(text[5:7]), int(text[8:10])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{day:02d} {_MONTHS[month - 1]} {year}"
        except (ValueError, IndexError):
            pass
    dt = to_local(value)
    return f"{dt.day:02d} {_MONTHS[dt.month - 1]} {dt.year}" if dt else "-"


def format_time(value: str | None) -> str:
    dt = to_local(value)
    return dt.strftime("%I:%M %p").lstrip("0") if dt else "-"


def format_datetime(value: str | None) -> str:
    dt = to_local(value)
    if not dt:
        return "-"
    return f"{dt.day:02d} {_MONTHS[dt.month - 1]} {dt.year}, {format_time(value)}"


def iso_date(date_value) -> str:
    """Normalize a date-like value to YYYY-MM-DD text."""
    text = str(date_value or "").strip()
    return text[:10] if len(text) >= 10 else text
