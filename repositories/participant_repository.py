"""Participant persistence."""

from __future__ import annotations

import sqlite3

from models.participant import Participant
from repositories.base import BaseRepository


class ParticipantRepository(BaseRepository):
    def create(self, data: dict, conn: sqlite3.Connection | None = None) -> int:
        cursor = self.db.execute(
            """INSERT INTO participants
               (full_name, email, phone, college, department, year, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data["full_name"], data.get("email", ""), data["phone"],
                data.get("college", ""), data.get("department", ""),
                data.get("year", ""), data["created_at"],
            ),
            conn=conn,
        )
        return int(cursor.lastrowid)

    def get_by_id(self, participant_id: int) -> Participant | None:
        row = self.db.query_one(
            "SELECT * FROM participants WHERE participant_id = ?", (participant_id,)
        )
        return Participant.from_row(row) if row else None

    def find_duplicate(
        self,
        phone: str,
        email: str = "",
        conn: sqlite3.Connection | None = None,
    ) -> Participant | None:
        clauses = ["phone = ?"]
        params: list = [phone.strip()]
        if email.strip():
            clauses.append("(email != '' AND email = ?)")
            params.append(email.strip())
        row = self.db.query_one(
            "SELECT * FROM participants WHERE " + " OR ".join(clauses)
            + " ORDER BY participant_id LIMIT 1",
            tuple(params),
            conn=conn,
        )
        return Participant.from_row(row) if row else None

    def search(self, query: str, limit: int = 50) -> list[Participant]:
        pattern = f"%{query.strip()}%"
        rows = self.db.query_all(
            """SELECT * FROM participants
               WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ? OR college LIKE ?
               ORDER BY participant_id DESC LIMIT ?""",
            (pattern, pattern, pattern, pattern, limit),
        )
        return [Participant.from_row(row) for row in rows]

    def get_all(self) -> list[Participant]:
        rows = self.db.query_all("SELECT * FROM participants ORDER BY participant_id DESC")
        return [Participant.from_row(row) for row in rows]

    def update(self, participant_id: int, data: dict) -> None:
        allowed = ("full_name", "email", "phone", "college", "department", "year")
        fields = [key for key in allowed if key in data]
        if not fields:
            return
        assignments = ", ".join(f"{key} = ?" for key in fields)
        self.db.execute(
            f"UPDATE participants SET {assignments} WHERE participant_id = ?",
            tuple(data[key] for key in fields) + (participant_id,),
        )

    def count(self) -> int:
        return int(self.db.scalar("SELECT COUNT(*) FROM participants") or 0)
