"""Append-only audit evidence for deterministic Triad role execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from governance.triad.contracts import Role


def now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class RoleExecutionAuditEvent:
    execution_id: str
    governance_task_id: str
    role: Role
    input_hash: str
    output_hash: str
    status: str
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)


class RoleExecutionAuditStore:
    """Append-only local audit store; independent from RuntimeManager/AuditLog."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS triad_role_audit ("
            "audit_id TEXT PRIMARY KEY, execution_id TEXT, governance_task_id TEXT, role TEXT, "
            "input_hash TEXT, output_hash TEXT, status TEXT, created_at TEXT)"
        )
        self._db.commit()

    @staticmethod
    def hash(value: object) -> str:
        encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def append(self, event: RoleExecutionAuditEvent) -> None:
        self._db.execute(
            "INSERT INTO triad_role_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event.audit_id, event.execution_id, event.governance_task_id, event.role.value,
             event.input_hash, event.output_hash, event.status, event.created_at),
        )
        self._db.commit()

    def get(self, audit_id: str) -> RoleExecutionAuditEvent | None:
        row = self._db.execute("SELECT * FROM triad_role_audit WHERE audit_id=?", (audit_id,)).fetchone()
        return self._from_row(row) if row else None

    def list(self) -> list[RoleExecutionAuditEvent]:
        rows = self._db.execute("SELECT * FROM triad_role_audit ORDER BY rowid").fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> RoleExecutionAuditEvent:
        return RoleExecutionAuditEvent(
            row["execution_id"], row["governance_task_id"], Role(row["role"]), row["input_hash"],
            row["output_hash"], row["status"], row["audit_id"], row["created_at"],
        )