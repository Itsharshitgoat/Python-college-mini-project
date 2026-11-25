"""Audit log persistence."""

from __future__ import annotations

import sqlite3

from repositories.base import BaseRepository
from utils.date_utils import utc_now_iso


class AuditRepository(BaseRepository):
    def log(
        self,
        action: str,
        details: str = "",
        user_id: int | None = None,
        event_id: int | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        self.db.execute(
            """INSERT INTO audit_logs (user_id, event_id, action, details, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, event_id, action, details, utc_now_iso()),
            conn=conn,
        )

    def recent(self, limit: int = 20) -> list[dict]:
        rows = self.db.query_all(
            """SELECT al.*, u.username, e.event_name
               FROM audit_logs al
               LEFT JOIN users u ON al.user_id = u.user_id
               LEFT JOIN events e ON al.event_id = e.event_id
               ORDER BY al.log_id DESC LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in rows]

    def count_failed_scans_today(self) -> int:
        return int(
            self.db.scalar(
                """SELECT COUNT(*) FROM audit_logs
                   WHERE action LIKE 'FAILED_SCAN%'
                     AND date(created_at, 'localtime') = date('now', 'localtime')"""
            )
            or 0
        )
