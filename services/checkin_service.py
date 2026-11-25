"""QR verification and atomic attendance recording."""

from __future__ import annotations

from database.connection import Database
from repositories.attendance_repository import AttendanceRepository
from repositories.audit_repository import AuditRepository
from repositories.registration_repository import RegistrationRepository
from services.qr_service import QrService
from utils.date_utils import format_time, utc_now_iso
from utils.result import Result, ResultCode


class CheckinService:
    """Applies the seven verification checks before writing attendance."""

    def __init__(
        self,
        db: Database,
        registrations: RegistrationRepository,
        attendance: AttendanceRepository,
        audit: AuditRepository,
        qr: QrService,
    ):
        self.db = db
        self.registrations = registrations
        self.attendance = attendance
        self.audit = audit
        self.qr = qr

    def verify_and_checkin(
        self, payload: str | None, event_id: int, operator_id: int | None = None
    ) -> Result:
        # 1. Correct QR format
        token = self.qr.parse(payload)
        if not token:
            return self._failed(
                ResultCode.INVALID_QR, "Invalid QR code. Unrecognized ticket format.",
                event_id, operator_id,
            )

        token_hash = self.qr.hash(token)

        # 2. Token hash exists
        registration = self.registrations.find_by_token_hash(token_hash)
        if not registration:
            return self._failed(
                ResultCode.UNREGISTERED_QR,
                "Unregistered QR code. No matching ticket found.",
                event_id, operator_id,
            )

        # 3 & 4. Registration and its event are still active
        if registration.registration_status != "ACTIVE":
            return self._failed(
                ResultCode.CANCELLED,
                "This registration has been cancelled.",
                event_id, operator_id, registration,
            )
        if registration.event_registration_status == "CANCELLED":
            return self._failed(
                ResultCode.CANCELLED,
                "This event has been cancelled.",
                event_id, operator_id, registration,
            )

        # 5. Event matches the selected event
        if registration.event_id != event_id:
            return self._failed(
                ResultCode.WRONG_EVENT,
                f"This ticket belongs to '{registration.event_name}'.",
                event_id, operator_id, registration,
            )

        # 6. Event permits check-in
        if registration.event_checkin_status != "OPEN":
            return self._failed(
                ResultCode.EVENT_CLOSED,
                "Check-in is not open for this event.",
                event_id, operator_id, registration,
            )

        try:
            with self.db.transaction() as conn:
                # Re-validate everything under the write lock.
                locked = self.registrations.find_by_token_hash(token_hash, conn=conn)
                if not locked or locked.registration_status != "ACTIVE":
                    raise _CheckinRejected(
                        ResultCode.CANCELLED, "This registration has been cancelled.", locked
                    )
                if locked.event_registration_status == "CANCELLED":
                    raise _CheckinRejected(
                        ResultCode.CANCELLED, "This event has been cancelled.", locked
                    )
                if locked.event_id != event_id:
                    raise _CheckinRejected(
                        ResultCode.WRONG_EVENT,
                        f"This ticket belongs to '{locked.event_name}'.",
                        locked,
                    )
                if locked.event_checkin_status != "OPEN":
                    raise _CheckinRejected(
                        ResultCode.EVENT_CLOSED,
                        "Check-in is not open for this event.",
                        locked,
                    )

                # 7. No existing attendance
                existing = conn.execute(
                    "SELECT * FROM attendance WHERE registration_id = ?",
                    (locked.registration_id,),
                ).fetchone()
                if existing:
                    return Result.fail(
                        ResultCode.ALREADY_CHECKED_IN,
                        f"{locked.full_name} already checked in at "
                        f"{format_time(existing['checked_in_at'])}.",
                        {
                            "registration": locked,
                            "checked_in_at": existing["checked_in_at"],
                        },
                    )

                checked_in_at = utc_now_iso()
                attendance_id = self.attendance.create(
                    int(locked.registration_id), operator_id, conn, checked_in_at
                )
                self.audit.log(
                    "SUCCESSFUL_CHECKIN",
                    f"REG-{locked.registration_id:06d} ({locked.full_name})",
                    user_id=operator_id,
                    event_id=event_id,
                    conn=conn,
                )
        except _CheckinRejected as exc:
            return self._failed(exc.code, exc.message, event_id, operator_id, exc.registration)
        except Exception as exc:  # pragma: no cover - defensive
            return Result.fail(ResultCode.ERROR, f"Check-in failed: {exc}")

        return Result.ok(
            "Check-in successful.",
            {
                "registration": registration,
                "attendance_id": attendance_id,
                "checked_in_at": checked_in_at,
            },
        )

    def _failed(
        self,
        code: str,
        message: str,
        event_id: int,
        operator_id: int | None,
        registration=None,
    ) -> Result:
        self.audit.log(
            f"FAILED_SCAN_{code}",
            message,
            user_id=operator_id,
            event_id=event_id,
        )
        return Result.fail(code, message, {"registration": registration} if registration else None)


class _CheckinRejected(Exception):
    def __init__(self, code: str, message: str, registration=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.registration = registration
