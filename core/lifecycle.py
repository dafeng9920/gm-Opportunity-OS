from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


STATES = ("EVALUATED", "SOURCE_ACQUIRED", "STATIC_REVIEWED", "WAITING_RUNTIME", "ACTIVE")
TRANSITIONS = {
    "EVALUATED": frozenset({"SOURCE_ACQUIRED"}),
    "SOURCE_ACQUIRED": frozenset({"STATIC_REVIEWED"}),
    "STATIC_REVIEWED": frozenset({"WAITING_RUNTIME"}),
    "WAITING_RUNTIME": frozenset(),
    "ACTIVE": frozenset(),
}


@dataclass(frozen=True, slots=True)
class ComponentLifecycleEvent:
    component_id: str
    previous_state: str
    new_state: str
    evidence_id: str
    timestamp: str = field(default_factory=utc_now)


class ComponentLifecycleLedger:
    """Append-only capability lifecycle ledger, separate from runtime activation."""
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS component_lifecycle (
                component_id TEXT NOT NULL, previous_state TEXT NOT NULL, new_state TEXT NOT NULL,
                evidence_id TEXT NOT NULL, timestamp TEXT NOT NULL)""")

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

    def current(self, component_id: str) -> str | None:
        with self._session() as db:
            row = db.execute("SELECT new_state FROM component_lifecycle WHERE component_id = ? ORDER BY rowid DESC LIMIT 1", (component_id,)).fetchone()
        return row["new_state"] if row else None

    def advance(self, component_id: str, new_state: str, evidence_id: str) -> ComponentLifecycleEvent:
        previous_state = self.current(component_id)
        if new_state not in STATES:
            raise ValueError("unknown lifecycle state")
        if previous_state is not None and new_state not in TRANSITIONS[previous_state]:
            raise ValueError(f"illegal lifecycle transition {previous_state} -> {new_state}")
        if previous_state is None and new_state != "EVALUATED":
            raise ValueError("lifecycle must begin at EVALUATED")
        event = ComponentLifecycleEvent(component_id, previous_state or "", new_state, evidence_id)
        with self._session() as db:
            db.execute("INSERT INTO component_lifecycle VALUES (?, ?, ?, ?, ?)", (event.component_id, event.previous_state, event.new_state, event.evidence_id, event.timestamp))
        return event

    def list(self, component_id: str | None = None) -> list[ComponentLifecycleEvent]:
        with self._session() as db:
            if component_id is None:
                rows = db.execute("SELECT component_id, previous_state, new_state, evidence_id, timestamp FROM component_lifecycle ORDER BY rowid").fetchall()
            else:
                rows = db.execute("SELECT component_id, previous_state, new_state, evidence_id, timestamp FROM component_lifecycle WHERE component_id = ? ORDER BY rowid", (component_id,)).fetchall()
        return [ComponentLifecycleEvent(**dict(row)) for row in rows]
