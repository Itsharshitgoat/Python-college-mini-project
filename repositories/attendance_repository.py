"""Attendance record persistence."""

from __future__ import annotations

import sqlite3

from models.attendance import Attendance
from repositories.base import BaseRepository

ATTENDANCE_SELECT = """
    SELECT a.*, r.registration_id AS reg_id,
           r.registration_status,
           p.full_name, p.phone,
           e.event_name, e.event_date,
           u.full_name AS operator_name,
           'REG-' || printf('%06d', r.registration_id) AS registration_code
    FROM attendance a
    JOIN registrations r ON a.registration_id = r.registration_id
    JOIN participants p ON r.participant_id = p.participant_id
    JOIN events e ON r.event_id = e.event_id
    LEFT JOIN users u ON a.operator_id = u.user_id
"""


class AttendanceRepository(BaseRepository):
    def create(
        self,
        registration_id: int,
        operator_id: int | None,
        conn: sqlite3.Connection,
        checked_in_at: str,
        status: str = "PRESENT",
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO attendance
               (registration_id, operator_id, checked_in_at, check_in_status)
               VALUES (?, ?, ?, ?)""",
            (registration_id, operator_id, checked_in_at, status),
            conn=conn,
        )
        return int(cursor.lastrowid)

    def find_by_registration(
        self, registration_id: int, conn: sqlite3.Connection | None = None
    ) -> Attendance | None:
        row = self.db.query_one(
            "SELECT * FROM attendance WHERE registration_id = ?",
            (registration_id,),
            conn=conn,
        )
        return Attendance.from_row(row) if row else None

    def list_for_event(self, event_id: int) -> list[Attendance]:
        rows = self.db.query_all(
            ATTENDANCE_SELECT + " WHERE r.event_id = ? ORDER BY a.checked_in_at DESC",
            (event_id,),
        )
        return [Attendance.from_row(row) for row in rows]

    def list_recent(self, limit: int = 8) -> list[Attendance]:
        rows = self.db.query_all(
            ATTENDANCE_SELECT + " ORDER BY a.checked_in_at DESC LIMIT ?", (limit,)
        )
        return [Attendance.from_row(row) for row in rows]

    def count_for_event(self, event_id: int) -> int:
        return int(
            self.db.scalar(
                """SELECT COUNT(*) FROM attendance a
                   JOIN registrations r ON a.registration_id = r.registration_id
                   WHERE r.event_id = ?""",
                (event_id,),
            )
            or 0
        )

    def count_today(self) -> int:
        return int(
            self.db.scalar(
                "SELECT COUNT(*) FROM attendance WHERE date(checked_in_at, 'localtime') = date('now', 'localtime')"
            )
            or 0
        )

    def checkin_by_hour(self) -> list[tuple[str, int]]:
        rows = self.db.query_all(
            """SELECT strftime('%H', checked_in_at, 'localtime') AS hour, COUNT(*) AS total
               FROM attendance GROUP BY hour ORDER BY hour"""
        )
        return [(f"{row['hour']}:00", int(row["total"])) for row in rows]

    def delete_by_registration(
        self, registration_id: int, conn: sqlite3.Connection | None = None
    ) -> None:
        self.db.execute(
            "DELETE FROM attendance WHERE registration_id = ?", (registration_id,), conn=conn
        )
