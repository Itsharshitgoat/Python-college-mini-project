"""Attendance record rules and manual check-in."""

from __future__ import annotations

from database.connection import Database
from repositories.attendance_repository import AttendanceRepository
from repositories.audit_repository import AuditRepository
from repositories.registration_repository import RegistrationRepository
from utils.date_utils import utc_now_iso
from utils.result import Result, ResultCode


class AttendanceService:
    def __init__(
        self,
        db: Database,
        attendance: AttendanceRepository,
        registrations: RegistrationRepository,
        audit: AuditRepository,
    ):
        self.db = db
        self.attendance = attendance
        self.registrations = registrations
        self.audit = audit

    def list_for_event(self, event_id: int) -> Result:
        return Result.ok(data=self.attendance.list_for_event(event_id))

    def today_count(self) -> int:
        return self.attendance.count_today()

    def summary(self, event_id: int) -> Result:
        return Result.ok(
            data={
                "total": self.registrations.count_for_event(event_id, active_only=True),
                "present": self.attendance.count_for_event(event_id),
                "pending": max(
                    self.registrations.count_for_event(event_id, active_only=True)
                    - self.attendance.count_for_event(event_id),
                    0,
                ),
            }
        )

    def manual_checkin(self, registration_id: int, operator_id: int | None = None) -> Result:
        registration = self.registrations.get_by_id(registration_id)
        if not registration:
            return Result.fail(ResultCode.NOT_FOUND, "Registration not found.")
        if registration.registration_status != "ACTIVE":
            return Result.fail(ResultCode.CANCELLED, "Registration is not active.")
        if registration.event_registration_status == "CANCELLED":
            return Result.fail(ResultCode.CANCELLED, "This event has been cancelled.")
        if self.attendance.find_by_registration(registration_id):
            return Result.fail(
                ResultCode.ALREADY_CHECKED_IN, "Participant is already checked in."
            )

        checked_in_at = utc_now_iso()
        try:
            with self.db.transaction() as conn:
                existing = conn.execute(
                    "SELECT attendance_id FROM attendance WHERE registration_id = ?",
                    (registration_id,),
                ).fetchone()
                if existing:
                    return Result.fail(
                        ResultCode.ALREADY_CHECKED_IN,
                        "Participant is already checked in.",
                    )
                self.attendance.create(
                    registration_id, operator_id, conn, checked_in_at, status="MANUAL"
                )
                self.audit.log(
                    "MANUAL_CHECKIN",
                    f"REG-{registration_id:06d} ({registration.full_name})",
                    user_id=operator_id,
                    event_id=registration.event_id,
                    conn=conn,
                )
        except Exception as exc:  # pragma: no cover - defensive
            return Result.fail(ResultCode.ERROR, f"Manual check-in failed: {exc}")
        return Result.ok("Participant marked present manually.")
