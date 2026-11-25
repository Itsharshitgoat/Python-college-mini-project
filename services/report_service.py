"""Dashboard statistics, analytics and CSV report generation."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from config import Paths
from database.connection import Database
from repositories.attendance_repository import AttendanceRepository
from repositories.audit_repository import AuditRepository
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from repositories.registration_repository import RegistrationRepository
from utils.date_utils import format_date, format_datetime, format_time
from utils.file_utils import safe_filename
from utils.result import Result, ResultCode


class ReportService:
    def __init__(
        self,
        db: Database,
        paths: Paths,
        events: EventRepository,
        participants: ParticipantRepository,
        registrations: RegistrationRepository,
        attendance: AttendanceRepository,
        audit: AuditRepository,
    ):
        self.db = db
        self.paths = paths
        self.events = events
        self.participants = participants
        self.registrations = registrations
        self.attendance = attendance
        self.audit = audit

    # --- dashboard -----------------------------------------------------
    def dashboard_metrics(self) -> dict:
        total_registrations = int(
            self.db.scalar("SELECT COUNT(*) FROM registrations WHERE registration_status='ACTIVE'")
            or 0
        )
        total_checkins = int(self.db.scalar("SELECT COUNT(*) FROM attendance") or 0)
        pending = int(
            self.db.scalar(
                """SELECT COUNT(*) FROM registrations r
                   LEFT JOIN attendance a ON r.registration_id = a.registration_id
                   WHERE r.registration_status='ACTIVE' AND a.attendance_id IS NULL"""
            )
            or 0
        )
        return {
            "total_events": self.events.count(),
            "total_participants": self.participants.count(),
            "total_registrations": total_registrations,
            "total_checkins": total_checkins,
            "pending": pending,
            "attendance_rate": round(
                (total_checkins / total_registrations * 100) if total_registrations else 0, 1
            ),
        }

    def recent_events(self, limit: int = 5) -> list:
        return self.events.get_all()[:limit]

    def recent_checkins(self, limit: int = 5) -> list:
        return self.attendance.list_recent(limit)

    def checkin_by_hour(self) -> list[tuple[str, int]]:
        return self.attendance.checkin_by_hour()

    def event_summary(self, event_id: int) -> Result:
        event = self.events.get_by_id(event_id)
        if not event:
            return Result.fail(ResultCode.NOT_FOUND, "Event not found.")
        return Result.ok(
            data={
                "event": event,
                "total": self.registrations.count_for_event(event_id, active_only=True),
                "present": self.attendance.count_for_event(event_id),
                "pending": event.pending_count,
                "failed_scans": self.audit.count_failed_scans_today(),
                "by_hour": self.attendance.checkin_by_hour(),
            }
        )

    # --- CSV exports ---------------------------------------------------
    def export_csv(self, kind: str, event_id: int | None = None) -> Result:
        exporters = {
            "attendance": self._attendance_rows,
            "pending": self._pending_rows,
            "participants": self._participant_rows,
            "registrations": self._registration_rows,
            "event_summary": self._event_rows,
        }
        exporter = exporters.get(kind)
        if not exporter:
            return Result.fail(ResultCode.INVALID_INPUT, "Unknown report type.")
        header, rows = exporter(event_id)
        if not rows:
            return Result.fail(ResultCode.NOT_FOUND, "No records to export.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        event_part = f"event_{event_id}_" if event_id else ""
        custom_dir = self.db.scalar(
            "SELECT setting_value FROM application_settings WHERE setting_key = 'export_directory'"
        )
        export_dir = (
            Path(custom_dir).expanduser()
            if custom_dir and str(custom_dir).strip()
            else self.paths.exports_dir
        )
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{event_part}{kind}_{timestamp}.csv"
        try:
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerows(rows)
        except OSError as exc:
            return Result.fail(ResultCode.ERROR, f"Could not write report: {exc}")
        self.audit.log("REPORT_EXPORTED", f"{kind} -> {path.name}", event_id=event_id)
        return Result.ok(f"Report saved to {path.name}", {"path": path})

    def _attendance_rows(self, event_id: int | None):
        header = [
            "Registration", "Name", "Phone", "Event", "Event Date",
            "Checked In (UTC)", "Status", "Operator",
        ]
        rows = []
        records = (
            self.attendance.list_for_event(event_id)
            if event_id
            else self.attendance.list_recent(1_000_000)
        )
        for item in records:
            rows.append(
                [
                    item.registration_code, item.full_name, item.phone,
                    item.event_name, item.event_date, item.checked_in_at,
                    item.check_in_status, item.operator_name,
                ]
            )
        return header, rows

    def _pending_rows(self, event_id: int | None):
        header = ["Registration", "Name", "Phone", "Email", "Event", "Registered (UTC)"]
        rows = []
        for item in self.registrations.list_for_event(event_id, filter_status="pending"):
            rows.append(
                [item.code, item.full_name, item.phone, item.email,
                 item.event_name, item.registered_at]
            )
        return header, rows

    def _participant_rows(self, event_id: int | None):
        header = ["Name", "Email", "Phone", "College", "Department", "Year"]
        rows = []
        if event_id:
            for item in self.registrations.list_for_event(event_id):
                rows.append(
                    [item.full_name, item.email, item.phone, item.college,
                     item.department, item.year]
                )
        else:
            for item in self.participants.get_all():
                rows.append(
                    [item.full_name, item.email, item.phone, item.college,
                     item.department, item.year]
                )
        return header, rows

    def _registration_rows(self, event_id: int | None):
        header = [
            "Registration", "Name", "Phone", "Event", "Status",
            "Registered (UTC)", "Checked In (UTC)",
        ]
        rows = []
        for item in self.registrations.list_for_event(event_id):
            rows.append(
                [
                    item.code, item.full_name, item.phone, item.event_name,
                    item.registration_status, item.registered_at,
                    format_datetime(item.checked_in_at) if item.checked_in_at else "",
                ]
            )
        return header, rows

    def _event_rows(self, event_id: int | None):
        header = [
            "Event", "Date", "Venue", "Capacity", "Registration Status",
            "Check-in Status", "Registered", "Checked In", "Pending",
        ]
        events = [self.events.get_by_id(event_id)] if event_id else self.events.get_all()
        rows = []
        for event in events:
            if not event:
                continue
            rows.append(
                [
                    event.event_name, event.event_date, event.venue, event.capacity,
                    event.registration_status, event.checkin_status,
                    event.registered_count, event.attended_count, event.pending_count,
                ]
            )
        return header, rows
