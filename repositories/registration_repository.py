"""Registration persistence and transactional capacity checks."""

from __future__ import annotations

import sqlite3

from models.registration import Registration
from repositories.base import BaseRepository

REGISTRATION_SELECT = """
    SELECT r.*,
           p.full_name, p.email, p.phone, p.college, p.department, p.year,
           e.event_name, e.event_date, e.venue,
           e.registration_status AS event_registration_status,
           e.checkin_status AS event_checkin_status,
           a.attendance_id, a.checked_in_at
    FROM registrations r
    JOIN participants p ON r.participant_id = p.participant_id
    JOIN events e ON r.event_id = e.event_id
    LEFT JOIN attendance a ON r.registration_id = a.registration_id
"""


class RegistrationRepository(BaseRepository):
    def create(
        self,
        participant_id: int,
        event_id: int,
        token_hash: str,
        conn: sqlite3.Connection,
        ticket_path: str = "",
    ) -> int:
        cursor = self.db.execute(
            """INSERT INTO registrations
               (participant_id, event_id, qr_token_hash, registration_status,
                registered_at, ticket_path)
               VALUES (?, ?, ?, 'ACTIVE', ?, ?)""",
            (participant_id, event_id, token_hash, self._now(), ticket_path),
            conn=conn,
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _now() -> str:
        from utils.date_utils import utc_now_iso

        return utc_now_iso()

    def get_by_id(self, registration_id: int) -> Registration | None:
        row = self.db.query_one(
            REGISTRATION_SELECT + " WHERE r.registration_id = ?", (registration_id,)
        )
        return Registration.from_row(row) if row else None

    def find_by_token_hash(
        self, token_hash: str, conn: sqlite3.Connection | None = None
    ) -> Registration | None:
        row = self.db.query_one(
            REGISTRATION_SELECT + " WHERE r.qr_token_hash = ?", (token_hash,), conn=conn
        )
        return Registration.from_row(row) if row else None

    def find_by_participant_event(
        self,
        participant_id: int,
        event_id: int,
        conn: sqlite3.Connection | None = None,
    ) -> Registration | None:
        row = self.db.query_one(
            REGISTRATION_SELECT
            + " WHERE r.participant_id = ? AND r.event_id = ?",
            (participant_id, event_id),
            conn=conn,
        )
        return Registration.from_row(row) if row else None

    def count_for_event(
        self,
        event_id: int,
        active_only: bool = True,
        conn: sqlite3.Connection | None = None,
    ) -> int:
        sql = "SELECT COUNT(*) FROM registrations WHERE event_id = ?"
        params: tuple = (event_id,)
        if active_only:
            sql += " AND registration_status = 'ACTIVE'"
        return int(self.db.scalar(sql, params, conn=conn) or 0)

    def list_for_event(
        self,
        event_id: int | None = None,
        search: str = "",
        filter_status: str = "all",
    ) -> list[Registration]:
        sql = REGISTRATION_SELECT
        params: list = []
        clauses: list[str] = []
        if event_id is not None:
            clauses.append("r.event_id = ?")
            params.append(event_id)
        if filter_status == "present":
            clauses.append("a.attendance_id IS NOT NULL AND r.registration_status = 'ACTIVE'")
        elif filter_status == "pending":
            clauses.append("a.attendance_id IS NULL AND r.registration_status = 'ACTIVE'")
        elif filter_status == "cancelled":
            clauses.append("r.registration_status = 'CANCELLED'")
        if search.strip():
            clauses.append("(p.full_name LIKE ? OR p.phone LIKE ? OR r.registration_id LIKE ?)")
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY r.registration_id DESC"
        return [Registration.from_row(row) for row in self.db.query_all(sql, tuple(params))]

    def list_for_participant(self, participant_id: int) -> list[Registration]:
        rows = self.db.query_all(
            REGISTRATION_SELECT + " WHERE r.participant_id = ? ORDER BY r.registered_at DESC",
            (participant_id,),
        )
        return [Registration.from_row(row) for row in rows]

    def list_recent(self, limit: int = 8) -> list[Registration]:
        rows = self.db.query_all(
            REGISTRATION_SELECT + " ORDER BY r.registered_at DESC LIMIT ?", (limit,)
        )
        return [Registration.from_row(row) for row in rows]

    def update_status(
        self, registration_id: int, status: str, conn: sqlite3.Connection | None = None
    ) -> None:
        self.db.execute(
            "UPDATE registrations SET registration_status = ? WHERE registration_id = ?",
            (status, registration_id),
            conn=conn,
        )

    def rotate_token(
        self, registration_id: int, token_hash: str, conn: sqlite3.Connection
    ) -> None:
        self.db.execute(
            "UPDATE registrations SET qr_token_hash = ? WHERE registration_id = ?",
            (token_hash, registration_id),
            conn=conn,
        )

    def set_ticket_path(self, registration_id: int, path: str) -> None:
        self.db.execute(
            "UPDATE registrations SET ticket_path = ? WHERE registration_id = ?",
            (path, registration_id),
        )

    def delete(self, registration_id: int, conn: sqlite3.Connection | None = None) -> None:
        self.db.execute(
            "DELETE FROM registrations WHERE registration_id = ?", (registration_id,), conn=conn
        )
