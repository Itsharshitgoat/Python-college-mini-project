"""Dashboard and reporting operations exposed to the UI."""

from __future__ import annotations

from services.backup_service import BackupService
from services.report_service import ReportService


class ReportController:
    def __init__(self, reports: ReportService, backup: BackupService):
        self.reports = reports
        self.backup = backup

    def dashboard(self) -> dict:
        return self.reports.dashboard_metrics()

    def recent_events(self, limit: int = 5):
        return self.reports.recent_events(limit)

    def recent_checkins(self, limit: int = 5):
        return self.reports.recent_checkins(limit)

    def event_summary(self, event_id: int):
        return self.reports.event_summary(event_id)

    def checkin_by_hour(self):
        return self.reports.checkin_by_hour()

    def export(self, kind: str, event_id: int | None = None):
        return self.reports.export_csv(kind, event_id)

    def create_backup(self):
        return self.backup.create_backup()

    def list_backups(self):
        return self.backup.list_backups()
