from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from core.schemas import HandoffItem


class HandoffQueue:
    """Traceable local producer-to-consumer handoff; no distribution implied."""
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS handoffs (
                id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, producer TEXT NOT NULL,
                consumer TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL)""")

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

    def enqueue(self, item: HandoffItem) -> None:
        with self._session() as db:
            db.execute("INSERT INTO handoffs VALUES (?, ?, ?, ?, ?, ?)",
                       (item.id, item.candidate_id, item.producer, item.consumer, item.created_at, item.status))

    def pending_for(self, consumer: str) -> list[HandoffItem]:
        with self._session() as db:
            rows = db.execute("SELECT * FROM handoffs WHERE consumer = ? AND status = 'pending' ORDER BY created_at", (consumer,)).fetchall()
        return [HandoffItem(**dict(row)) for row in rows]


