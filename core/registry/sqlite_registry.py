from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from core.schemas import AdapterRegistration, Component, RuntimeRegistration


class ComponentRegistry:
    """SQLite-backed source of truth for Components, Adapters, and Runtimes."""
    def __init__(self, database: Path | str) -> None:
        self.database = str(database)
        self._create_table()

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

    def _create_table(self) -> None:
        with self._session() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS components (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
                version TEXT NOT NULL, status TEXT NOT NULL, capability TEXT NOT NULL,
                created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS adapters (
                adapter_id TEXT PRIMARY KEY, backend_component TEXT NOT NULL,
                version TEXT NOT NULL, permission_profile TEXT NOT NULL,
                contract TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                FOREIGN KEY(adapter_id) REFERENCES components(id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS runtimes (
                runtime_id TEXT PRIMARY KEY, name TEXT NOT NULL, runtime_type TEXT NOT NULL,
                version TEXT NOT NULL, policy TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, FOREIGN KEY(runtime_id) REFERENCES components(id))""")

    def register(self, component: Component) -> None:
        with self._session() as db:
            db.execute("INSERT INTO components VALUES (?, ?, ?, ?, ?, ?, ?)", tuple(component.to_dict().values()))

    def get(self, component_id: str) -> Component | None:
        with self._session() as db:
            row = db.execute("SELECT * FROM components WHERE id = ?", (component_id,)).fetchone()
        return Component(**dict(row)) if row else None

    def list(self) -> list[Component]:
        with self._session() as db:
            rows = db.execute("SELECT * FROM components ORDER BY created_at, id").fetchall()
        return [Component(**dict(row)) for row in rows]

    def update_status(self, component_id: str, status: str) -> None:
        with self._session() as db:
            result = db.execute("UPDATE components SET status = ? WHERE id = ?", (status, component_id))
            if result.rowcount != 1:
                raise KeyError(f"component not found: {component_id}")

    def delete(self, component_id: str) -> None:
        with self._session() as db:
            result = db.execute("DELETE FROM components WHERE id = ?", (component_id,))
            if result.rowcount != 1:
                raise KeyError(f"component not found: {component_id}")

    def register_adapter(self, adapter: AdapterRegistration) -> None:
        component = self.get(adapter.adapter_id)
        if component is None or component.type != "adapter":
            raise ValueError("adapter registration requires a Component of type adapter")
        with self._session() as db:
            db.execute("INSERT INTO adapters VALUES (?, ?, ?, ?, ?, ?, ?)", (adapter.adapter_id, adapter.backend_component, adapter.version, adapter.permission_profile, adapter.contract, adapter.status, adapter.created_at))

    def get_adapter(self, adapter_id: str) -> AdapterRegistration | None:
        with self._session() as db:
            row = db.execute("SELECT * FROM adapters WHERE adapter_id = ?", (adapter_id,)).fetchone()
        return AdapterRegistration(**dict(row)) if row else None

    def register_runtime(self, runtime: RuntimeRegistration) -> None:
        component = self.get(runtime.runtime_id)
        if component is None or component.type != "runtime":
            raise ValueError("runtime registration requires a Component of type runtime")
        with self._session() as db:
            db.execute("INSERT INTO runtimes VALUES (?, ?, ?, ?, ?, ?, ?)", (runtime.runtime_id, runtime.name, runtime.runtime_type, runtime.version, runtime.policy, runtime.status, runtime.created_at))

    def get_runtime(self, runtime_id: str) -> RuntimeRegistration | None:
        with self._session() as db:
            row = db.execute("SELECT * FROM runtimes WHERE runtime_id = ?", (runtime_id,)).fetchone()
        return RuntimeRegistration(**dict(row)) if row else None

    def list_adapters(self) -> list[AdapterRegistration]:
        with self._session() as db:
            rows = db.execute("SELECT * FROM adapters ORDER BY adapter_id").fetchall()
        return [AdapterRegistration(**dict(row)) for row in rows]

    def list_runtimes(self) -> list[RuntimeRegistration]:
        with self._session() as db:
            rows = db.execute("SELECT * FROM runtimes ORDER BY runtime_id").fetchall()
        return [RuntimeRegistration(**dict(row)) for row in rows]
