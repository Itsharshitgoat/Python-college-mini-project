"""Attendance operations exposed to the UI."""

from __future__ import annotations

from services.attendance_service import AttendanceService
from services.report_service import ReportService


class AttendanceController:
    def __init__(self, attendance: AttendanceService, reports: ReportService):
        self.attendance = attendance
        self.reports = reports

    def list_for_event(self, event_id: int):
        return self.attendance.list_for_event(event_id)

    def summary(self, event_id: int):
        return self.attendance.summary(event_id)

    def today_count(self) -> int:
        return self.attendance.today_count()

    def manual_checkin(self, registration_id: int, operator_id: int | None):
        return self.attendance.manual_checkin(registration_id, operator_id)

    def export(self, kind: str, event_id: int):
        return self.reports.export_csv(kind, event_id)
