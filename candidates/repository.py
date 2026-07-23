from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from core.schemas import CandidatePacket
from core.state import CandidateStateMachine


class CandidateRepository:
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, signal TEXT NOT NULL,
                evidence_ids TEXT NOT NULL, source TEXT NOT NULL, confidence REAL NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL)""")

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

    def create(self, packet: CandidatePacket) -> None:
        CandidateStateMachine(packet.status)
        with self._session() as db:
            db.execute("INSERT INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                packet.id, packet.title, packet.signal, json.dumps(packet.evidence_ids),
                packet.source, packet.confidence, packet.status, packet.created_at,
            ))

    def get(self, candidate_id: str) -> CandidatePacket | None:
        with self._session() as db:
            row = db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["evidence_ids"] = tuple(json.loads(data["evidence_ids"]))
        return CandidatePacket(**data)

    def transition(self, candidate_id: str, next_status: str) -> CandidatePacket:
        packet = self.get(candidate_id)
        if not packet:
            raise KeyError(f"candidate not found: {candidate_id}")
        CandidateStateMachine(packet.status).transition_to(next_status)
        with self._session() as db:
            db.execute("UPDATE candidates SET status = ? WHERE id = ?", (next_status, candidate_id))
        return CandidatePacket(**{**packet.to_dict(), "status": next_status, "evidence_ids": packet.evidence_ids})


