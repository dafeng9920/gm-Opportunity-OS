from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ContractRegistration:
    id: str
    version: str
    direction: str
    description: str


class ContractRegistry:
    """Explicit contract definitions; adapters reference these IDs but do not define them."""
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        with self._session() as db:
            db.execute("CREATE TABLE IF NOT EXISTS contracts (id TEXT PRIMARY KEY, version TEXT NOT NULL, direction TEXT NOT NULL, description TEXT NOT NULL)")

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

    def register(self, contract: ContractRegistration) -> None:
        with self._session() as db:
            db.execute("INSERT INTO contracts VALUES (?, ?, ?, ?)", (contract.id, contract.version, contract.direction, contract.description))

    def list(self) -> list[ContractRegistration]:
        with self._session() as db:
            rows = db.execute("SELECT * FROM contracts ORDER BY id").fetchall()
        return [ContractRegistration(**dict(row)) for row in rows]
