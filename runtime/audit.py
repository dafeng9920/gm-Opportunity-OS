from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class AuditEvent:
    caller: str
    adapter_id: str
    runtime_id: str
    input_hash: str
    output_hash: str
    decision: str
    external_version: str = ""
    execution_ms: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=utc_now)


class AuditLog:
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS runtime_audit (
                id TEXT PRIMARY KEY, caller TEXT NOT NULL, adapter_id TEXT NOT NULL, runtime_id TEXT NOT NULL,
                input_hash TEXT NOT NULL, output_hash TEXT NOT NULL, decision TEXT NOT NULL, external_version TEXT NOT NULL DEFAULT "",
                execution_ms INTEGER NOT NULL DEFAULT 0, timestamp TEXT NOT NULL)""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(runtime_audit)").fetchall()}
            if "external_version" not in columns:
                db.execute("ALTER TABLE runtime_audit ADD COLUMN external_version TEXT NOT NULL DEFAULT \"\"")
            if "execution_ms" not in columns:
                db.execute("ALTER TABLE runtime_audit ADD COLUMN execution_ms INTEGER NOT NULL DEFAULT 0")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def append(self, event: AuditEvent) -> None:
        with self._session() as db:
            db.execute("INSERT INTO runtime_audit (id, caller, adapter_id, runtime_id, input_hash, output_hash, decision, external_version, execution_ms, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (event.id, event.caller, event.adapter_id, event.runtime_id, event.input_hash, event.output_hash, event.decision, event.external_version, event.execution_ms, event.timestamp))

    def list(self) -> list[AuditEvent]:
        with self._session() as db:
            rows = db.execute("SELECT id, caller, adapter_id, runtime_id, input_hash, output_hash, decision, external_version, execution_ms, timestamp FROM runtime_audit ORDER BY timestamp, id").fetchall()
        return [AuditEvent(**dict(row)) for row in rows]
