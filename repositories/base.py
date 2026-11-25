"""Shared repository base."""

from __future__ import annotations

import sqlite3
from typing import Any

from database.connection import Database


class BaseRepository:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _values(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None
