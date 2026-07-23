from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class GovernanceAuditLedger:
    """Append-only local audit of governance actions; it does not alter Core records."""

    def __init__(self, db_path: Path) -> None:
        self._connection = sqlite3.connect(db_path)
        self._connection.execute("CREATE TABLE IF NOT EXISTS governance_audit (task_id TEXT, role TEXT, action TEXT, decision TEXT, created_at TEXT)")

    def append(self, task_id: str, role: str, action: str, decision: str = "") -> None:
        self._connection.execute(
            "INSERT INTO governance_audit VALUES (?, ?, ?, ?, ?)",
            (task_id, role, action, decision, datetime.now(UTC).isoformat()),
        )
        self._connection.commit()
