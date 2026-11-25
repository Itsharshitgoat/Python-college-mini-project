"""Event persistence."""

from __future__ import annotations

import sqlite3

from models.event import Event
from repositories.base import BaseRepository

EVENT_SELECT = """
    SELECT e.*,
        (SELECT COUNT(*) FROM registrations r WHERE r.event_id = e.event_id) AS registered_count,
        (SELECT COUNT(*) FROM attendance a
            JOIN registrations r2 ON a.registration_id = r2.registration_id
            WHERE r2.event_id = e.event_id) AS attended_count
    FROM events e
"""


class EventRepository(BaseRepository):
    def create(self, data: dict, conn: sqlite3.Connection | None = None) -> int:
        cursor = self.db.execute(
            """INSERT INTO events
               (event_name, description, event_date, start_time, end_time, venue,
                capacity, registration_status, checkin_status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["event_name"], data.get("description", ""), data["event_date"],
                data.get("start_time", ""), data.get("end_time", ""), data["venue"],
                int(data["capacity"]), data.get("registration_status", "DRAFT"),
                data.get("checkin_status", "DISABLED"), data["created_at"],
            ),
            conn=conn,
        )
        return int(cursor.lastrowid)

    def update(self, event_id: int, data: dict, conn: sqlite3.Connection | None = None) -> None:
        allowed = (
            "event_name", "description", "event_date", "start_time", "end_time",
            "venue", "capacity", "registration_status", "checkin_status",
        )
        fields = [key for key in allowed if key in data]
        if not fields:
            return
        assignments = ", ".join(f"{key} = ?" for key in fields)
        self.db.execute(
            f"UPDATE events SET {assignments} WHERE event_id = ?",
            tuple(data[key] for key in fields) + (event_id,),
            conn=conn,
        )

    def set_status(
        self, event_id: int, column: str, value: str, conn: sqlite3.Connection | None = None
    ) -> None:
        if column not in ("registration_status", "checkin_status"):
            raise ValueError("Invalid status column")
        self.db.execute(
            f"UPDATE events SET {column} = ? WHERE event_id = ?",
            (value, event_id),
            conn=conn,
        )

    def get_by_id(self, event_id: int) -> Event | None:
        row = self.db.query_one(EVENT_SELECT + " WHERE e.event_id = ?", (event_id,))
        return Event.from_row(row) if row else None

    def get_all(self, search: str = "", status: str | None = None) -> list[Event]:
        sql = EVENT_SELECT
        params: list = []
        clauses = []
        if search:
            clauses.append("(e.event_name LIKE ? OR e.venue LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if status and status != "All Events":
            clauses.append("e.registration_status = ?")
            params.append(status)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY e.event_date DESC, e.event_id DESC"
        return [Event.from_row(row) for row in self.db.query_all(sql, tuple(params))]

    def count(self) -> int:
        return int(self.db.scalar("SELECT COUNT(*) FROM events") or 0)

    def delete(self, event_id: int) -> None:
        self.db.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
