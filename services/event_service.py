"""Event business rules."""

from __future__ import annotations

import shutil
from pathlib import Path

from config import CHECKIN_STATUSES, EVENT_STATUSES, Paths
from repositories.audit_repository import AuditRepository
from repositories.event_repository import EventRepository
from utils.date_utils import utc_now_iso
from utils.result import Result, ResultCode
from utils.validators import validate_event_form


class EventService:
    def __init__(
        self,
        event_repo: EventRepository,
        audit_repo: AuditRepository,
        paths: Paths | None = None,
    ):
        self.events = event_repo
        self.audit = audit_repo
        self.paths = paths

    def create(self, form: dict, user_id: int | None = None) -> Result:
        error = validate_event_form(form)
        if error:
            return Result.fail(ResultCode.INVALID_INPUT, error)
        event_id = self.events.create(
            {
                **form,
                "registration_status": form.get("registration_status", "DRAFT"),
                "checkin_status": form.get("checkin_status", "DISABLED"),
                "created_at": utc_now_iso(),
            }
        )
        self.audit.log(
            "EVENT_CREATED",
            f"Created event '{form['event_name']}' (ID {event_id})",
            user_id=user_id,
            event_id=event_id,
        )
        return Result.ok("Event created successfully.", {"event_id": event_id})

    def update(self, event_id: int, form: dict, user_id: int | None = None) -> Result:
        if not self.events.get_by_id(event_id):
            return Result.fail(ResultCode.NOT_FOUND, "Event not found.")
        error = validate_event_form(form)
        if error:
            return Result.fail(ResultCode.INVALID_INPUT, error)
        self.events.update(event_id, form)
        self.audit.log("EVENT_UPDATED", f"Updated event ID {event_id}", user_id, event_id)
        return Result.ok("Event updated successfully.")

    def set_status(
        self, event_id: int, column: str, value: str, user_id: int | None = None
    ) -> Result:
        allowed = EVENT_STATUSES if column == "registration_status" else CHECKIN_STATUSES
        if value not in allowed:
            return Result.fail(ResultCode.INVALID_INPUT, f"Invalid status '{value}'.")
        if not self.events.get_by_id(event_id):
            return Result.fail(ResultCode.NOT_FOUND, "Event not found.")
        self.events.set_status(event_id, column, value)
        self.audit.log(
            "EVENT_STATUS_CHANGED", f"{column} -> {value}", user_id, event_id
        )
        return Result.ok("Event status updated.")

    def list_events(self, search: str = "", status: str | None = None) -> Result:
        return Result.ok(data=self.events.get_all(search=search, status=status))

    def get_event(self, event_id: int) -> Result:
        event = self.events.get_by_id(event_id)
        if not event:
            return Result.fail(ResultCode.NOT_FOUND, "Event not found.")
        return Result.ok(data=event)

    def delete(self, event_id: int, user_id: int | None = None) -> Result:
        event = self.events.get_by_id(event_id)
        if not event:
            return Result.fail(ResultCode.NOT_FOUND, "Event not found.")
        self.events.delete(event_id)
        if self.paths:
            qr_dir = self.paths.qr_dir / f"event_{event_id}"
            if qr_dir.exists() and qr_dir.is_dir():
                shutil.rmtree(qr_dir, ignore_errors=True)
        # The event row is gone, so keep the ID in the audit text instead of
        # referencing it through the audit_logs.event_id foreign key.
        self.audit.log(
            "EVENT_DELETED",
            f"Deleted event '{event.event_name}' (ID {event_id})",
            user_id=user_id,
        )
        return Result.ok("Event deleted.")
