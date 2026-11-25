"""Application user persistence."""

from __future__ import annotations

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def get_by_username(self, username: str) -> User | None:
        row = self.db.query_one(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),)
        )
        return User.from_row(row) if row else None

    def get_by_id(self, user_id: int) -> User | None:
        row = self.db.query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return User.from_row(row) if row else None

    def get_all(self) -> list[User]:
        rows = self.db.query_all("SELECT * FROM users ORDER BY user_id")
        return [User.from_row(row) for row in rows]

    def create(self, data: dict) -> int:
        cursor = self.db.execute(
            """INSERT INTO users (username, password_hash, full_name, role, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (
                data["username"], data["password_hash"], data.get("full_name", ""),
                data["role"], data["created_at"],
            ),
        )
        return int(cursor.lastrowid)

    def set_password(self, user_id: int, password_hash: str) -> None:
        self.db.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?", (password_hash, user_id)
        )

    def set_active(self, user_id: int, active: bool) -> None:
        self.db.execute(
            "UPDATE users SET is_active = ? WHERE user_id = ?", (1 if active else 0, user_id)
        )

    def update(self, user_id: int, data: dict) -> None:
        allowed = ("full_name", "role")
        fields = [key for key in allowed if key in data]
        if not fields:
            return
        assignments = ", ".join(f"{key} = ?" for key in fields)
        self.db.execute(
            f"UPDATE users SET {assignments} WHERE user_id = ?",
            tuple(data[key] for key in fields) + (user_id,),
        )

    def count(self) -> int:
        return int(self.db.scalar("SELECT COUNT(*) FROM users") or 0)
