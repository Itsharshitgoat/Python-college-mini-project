"""Thread-safe SQLite connection management."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class Database:
    """
    Owns one shared SQLite connection guarded by a re-entrant lock.

    Repositories may pass an explicit ``conn`` (inside a transaction) so that
    all statements participate in the same atomic unit of work.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.RLock()

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=30
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA busy_timeout = 30000")
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a block inside BEGIN IMMEDIATE ... COMMIT / ROLLBACK."""
        with self._lock:
            conn = self.connect()
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def execute(
        self, sql: str, params: Any = (), conn: sqlite3.Connection | None = None
    ) -> sqlite3.Cursor:
        if conn is not None:
            return conn.execute(sql, params)
        with self._lock:
            connection = self.connect()
            cursor = connection.execute(sql, params)
            connection.commit()
            return cursor

    def query_one(
        self, sql: str, params: Any = (), conn: sqlite3.Connection | None = None
    ) -> sqlite3.Row | None:
        if conn is not None:
            return conn.execute(sql, params).fetchone()
        with self._lock:
            return self.connect().execute(sql, params).fetchone()

    def query_all(
        self, sql: str, params: Any = (), conn: sqlite3.Connection | None = None
    ) -> list[sqlite3.Row]:
        if conn is not None:
            return conn.execute(sql, params).fetchall()
        with self._lock:
            return self.connect().execute(sql, params).fetchall()

    def scalar(
        self, sql: str, params: Any = (), conn: sqlite3.Connection | None = None
    ) -> Any:
        row = self.query_one(sql, params, conn=conn)
        return row[0] if row else None

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
