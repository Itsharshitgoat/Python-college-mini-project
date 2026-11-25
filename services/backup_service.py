"""Consistent SQLite database backups using the SQLite backup API."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from config import Paths
from database.connection import Database
from repositories.audit_repository import AuditRepository
from utils.result import Result, ResultCode


class BackupService:
    def __init__(self, db: Database, paths: Paths, audit: AuditRepository):
        self.db = db
        self.paths = paths
        self.audit = audit

    def create_backup(self) -> Result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.paths.backups_dir / f"backup_{timestamp}.db"
        try:
            source = self.db.connect()
            destination = sqlite3.connect(str(target))
            try:
                source.backup(destination)
            finally:
                destination.close()
        except sqlite3.Error as exc:
            return Result.fail(ResultCode.ERROR, f"Backup failed: {exc}")
        self.audit.log("DATABASE_BACKUP", target.name)
        return Result.ok(f"Backup saved to {target.name}", {"path": target})

    def list_backups(self) -> list[Path]:
        return sorted(
            self.paths.backups_dir.glob("backup_*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
