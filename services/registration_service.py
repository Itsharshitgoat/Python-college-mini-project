"""Registration rules: validation, capacity, duplicates and QR issuance."""

from __future__ import annotations

from pathlib import Path

from config import Paths
from database.connection import Database
from repositories.audit_repository import AuditRepository
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from repositories.registration_repository import RegistrationRepository
from services.qr_service import QrService
from utils.date_utils import utc_now_iso
from utils.result import Result, ResultCode
from utils.validators import validate_participant_form


class _RegistrationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class RegistrationService:
    def __init__(
        self,
        db: Database,
        paths: Paths,
        events: EventRepository,
        participants: ParticipantRepository,
        registrations: RegistrationRepository,
        qr: QrService,
        audit: AuditRepository,
    ):
        self.db = db
        self.paths = paths
        self.events = events
        self.participants = participants
        self.registrations = registrations
        self.qr = qr
        self.audit = audit

    def register(self, form: dict, user_id: int | None = None) -> Result:
        error = validate_participant_form(form)
        if error:
            return Result.fail(ResultCode.INVALID_INPUT, error)

        try:
            event_id = int(form.get("event_id"))
        except (TypeError, ValueError):
            return Result.fail(ResultCode.INVALID_INPUT, "Select a valid event.")

        event = self.events.get_by_id(event_id)
        if not event:
            return Result.fail(ResultCode.NOT_FOUND, "Selected event no longer exists.")
        if event.registration_status == "CANCELLED":
            return Result.fail(
                ResultCode.REGISTRATION_CLOSED,
                "This event has been cancelled.",
            )
        if event.registration_status != "OPEN":
            return Result.fail(
                ResultCode.REGISTRATION_CLOSED,
                "Registration for this event is not open.",
            )

        token = self.qr.new_token()
        payload = self.qr.payload(token)
        token_hash = self.qr.hash(token)
        try:
            self.qr.make_qr_image(payload)
        except Exception as exc:  # pragma: no cover - library failure path
            return Result.fail(ResultCode.ERROR, f"QR generation failed: {exc}")

        saved_path: Path | None = None
        reused_existing = False
        try:
            with self.db.transaction() as conn:
                # Re-read the event inside the write lock.
                fresh_event = conn.execute(
                    """SELECT event_name, event_date, venue, capacity, registration_status
                       FROM events WHERE event_id = ?""",
                    (event_id,),
                ).fetchone()
                if not fresh_event:
                    raise _RegistrationError(ResultCode.NOT_FOUND, "Event not found.")
                if fresh_event["registration_status"] == "CANCELLED":
                    raise _RegistrationError(
                        ResultCode.REGISTRATION_CLOSED,
                        "This event has been cancelled.",
                    )
                if fresh_event["registration_status"] != "OPEN":
                    raise _RegistrationError(
                        ResultCode.REGISTRATION_CLOSED,
                        "Registration for this event is not open.",
                    )

                duplicate_contact = self.participants.find_duplicate(
                    form["phone"], form.get("email", ""), conn=conn
                )
                if duplicate_contact:
                    participant_id = int(duplicate_contact.participant_id)
                    reused_existing = True
                else:
                    participant_id = self.participants.create(
                        {
                            **form,
                            "created_at": utc_now_iso(),
                        },
                        conn=conn,
                    )

                if self.registrations.find_by_participant_event(
                    participant_id, event_id, conn=conn
                ):
                    raise _RegistrationError(
                        ResultCode.DUPLICATE_REGISTRATION,
                        "This participant is already registered for the event.",
                    )

                active_count = self.registrations.count_for_event(
                    event_id, active_only=True, conn=conn
                )
                if active_count >= int(fresh_event["capacity"]):
                    raise _RegistrationError(
                        ResultCode.CAPACITY_REACHED,
                        "Event capacity has been reached.",
                    )

                registration_id = self.registrations.create(
                    participant_id, event_id, token_hash, conn
                )
                saved_path = self.qr.save_ticket_qr(registration_id, event_id, payload)
                conn.execute(
                    "UPDATE registrations SET ticket_path = ? WHERE registration_id = ?",
                    (str(saved_path), registration_id),
                )
                self.audit.log(
                    "PARTICIPANT_REGISTERED",
                    f"REG-{registration_id:06d} for {fresh_event['event_name']}",
                    user_id=user_id,
                    event_id=event_id,
                    conn=conn,
                )
        except _RegistrationError as exc:
            self._cleanup(saved_path)
            return Result.fail(exc.code, exc.message)
        except Exception as exc:
            self._cleanup(saved_path)
            return Result.fail(ResultCode.ERROR, f"Registration failed: {exc}")

        registration = self.registrations.get_by_id(registration_id)
        message = "Registration successful."
        if reused_existing:
            message += " Existing participant record reused."
        return Result.ok(
            message,
            {
                "registration": registration,
                "token": token,
                "payload": payload,
                "qr_path": saved_path,
            },
        )

    @staticmethod
    def _cleanup(path: Path | None) -> None:
        if path and path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    def reissue_ticket(self, registration_id: int, user_id: int | None = None) -> Result:
        registration = self.registrations.get_by_id(registration_id)
        if not registration:
            return Result.fail(ResultCode.NOT_FOUND, "Registration not found.")

        token = self.qr.new_token()
        payload = self.qr.payload(token)
        token_hash = self.qr.hash(token)
        saved_path: Path | None = None
        try:
            with self.db.transaction() as conn:
                current = conn.execute(
                    "SELECT registration_id FROM registrations WHERE registration_id = ?",
                    (registration_id,),
                ).fetchone()
                if not current:
                    raise _RegistrationError(ResultCode.NOT_FOUND, "Registration not found.")
                self.registrations.rotate_token(registration_id, token_hash, conn)
                saved_path = self.qr.save_ticket_qr(
                    registration_id, registration.event_id, payload
                )
                conn.execute(
                    "UPDATE registrations SET ticket_path = ? WHERE registration_id = ?",
                    (str(saved_path), registration_id),
                )
                self.audit.log(
                    "TICKET_REISSUED",
                    f"REG-{registration_id:06d} token rotated",
                    user_id=user_id,
                    event_id=registration.event_id,
                    conn=conn,
                )
        except _RegistrationError as exc:
            self._cleanup(saved_path)
            return Result.fail(exc.code, exc.message)
        except Exception as exc:
            self._cleanup(saved_path)
            return Result.fail(ResultCode.ERROR, f"Ticket reissue failed: {exc}")

        return Result.ok(
            "Ticket reissued. The previous QR token has been invalidated.",
            {
                "registration": self.registrations.get_by_id(registration_id),
                "token": token,
                "payload": payload,
                "qr_path": saved_path,
            },
        )

    def cancel(self, registration_id: int, user_id: int | None = None) -> Result:
        registration = self.registrations.get_by_id(registration_id)
        if not registration:
            return Result.fail(ResultCode.NOT_FOUND, "Registration not found.")
        self.registrations.update_status(registration_id, "CANCELLED")
        self.audit.log(
            "REGISTRATION_CANCELLED",
            f"REG-{registration_id:06d}",
            user_id=user_id,
            event_id=registration.event_id,
        )
        return Result.ok("Registration cancelled.")

    def delete_registration(self, registration_id: int, user_id: int | None = None) -> Result:
        """Permanently remove one participant from one event.

        The participant master record is kept because it can be reused by other
        events. Attendance is removed by the schema's cascade rule, and the
        ticket image is deleted after the transaction commits.
        """
        try:
            registration_id = int(registration_id)
        except (TypeError, ValueError):
            return Result.fail(ResultCode.INVALID_INPUT, "Invalid registration.")

        participant_name = ""
        event_id: int | None = None
        event_name = ""
        ticket_path = ""
        try:
            with self.db.transaction() as conn:
                row = conn.execute(
                    """SELECT r.event_id, r.ticket_path, p.full_name, e.event_name
                       FROM registrations r
                       JOIN participants p ON r.participant_id = p.participant_id
                       JOIN events e ON r.event_id = e.event_id
                       WHERE r.registration_id = ?""",
                    (registration_id,),
                ).fetchone()
                if not row:
                    raise _RegistrationError(
                        ResultCode.NOT_FOUND, "Registration not found."
                    )
                event_id = int(row["event_id"])
                event_name = row["event_name"]
                participant_name = row["full_name"]
                ticket_path = row["ticket_path"] or ""

                self.registrations.delete(registration_id, conn=conn)
                self.audit.log(
                    "REGISTRATION_DELETED",
                    (
                        f"Removed REG-{registration_id:06d} ({participant_name}) "
                        f"from '{event_name}' (ID {event_id})"
                    ),
                    user_id=user_id,
                    event_id=event_id,
                    conn=conn,
                )
        except _RegistrationError as exc:
            return Result.fail(exc.code, exc.message)
        except Exception as exc:
            return Result.fail(ResultCode.ERROR, f"Could not remove participant: {exc}")

        self._cleanup(Path(ticket_path) if ticket_path else None)
        return Result.ok(
            f"{participant_name} removed from {event_name}.",
            {"event_id": event_id, "registration_id": registration_id},
        )

    def list_for_event(
        self, event_id: int, search: str = "", filter_status: str = "all"
    ) -> Result:
        return Result.ok(
            data=self.registrations.list_for_event(event_id, search, filter_status)
        )

    def list_for_participant(self, participant_id: int) -> Result:
        return Result.ok(
            data=self.registrations.list_for_participant(participant_id)
        )

    def get(self, registration_id: int) -> Result:
        registration = self.registrations.get_by_id(registration_id)
        return (
            Result.ok(data=registration)
            if registration
            else Result.fail(ResultCode.NOT_FOUND, "Registration not found.")
        )
