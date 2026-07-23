from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from core.schemas import EvidenceObject


class EvidenceLedger:
    """Append-only storage for original external evidence."""
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, source_type TEXT NOT NULL,
                captured_time TEXT NOT NULL, raw_reference TEXT NOT NULL,
                content_hash TEXT NOT NULL, metadata TEXT NOT NULL)""")

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

    def append(self, evidence: EvidenceObject) -> None:
        with self._session() as db:
            db.execute("INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?)", (
                evidence.id, evidence.source, evidence.source_type, evidence.captured_time,
                evidence.raw_reference, evidence.content_hash,
                json.dumps(evidence.metadata, sort_keys=True),
            ))

    def get(self, evidence_id: str) -> EvidenceObject | None:
        with self._session() as db:
            row = db.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["metadata"] = json.loads(data.pop("metadata"))
        return EvidenceObject(**data)


