"""Independent SQLite registry for Consumer identities and capabilities; no packet access."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .contracts import ConsumerAction, ConsumerCapability, ConsumerIdentity, ConsumerType
class ConsumerRegistry:
    def __init__(self, database: Path | str) -> None:
        self._db=sqlite3.connect(database); self._db.row_factory=sqlite3.Row
        self._db.execute('CREATE TABLE IF NOT EXISTS consumers (consumer_id TEXT, version TEXT, consumer_type TEXT, created_at TEXT, PRIMARY KEY(consumer_id, version))')
        self._db.execute('CREATE TABLE IF NOT EXISTS consumer_capabilities (consumer_id TEXT, version TEXT, actions TEXT, packet_versions TEXT, purpose TEXT, PRIMARY KEY(consumer_id, version))')
    def close(self) -> None:
        self._db.close()
    def register(self, identity: ConsumerIdentity, capability: ConsumerCapability) -> None:
        if identity.consumer_id != capability.consumer_id or identity.version != capability.version: raise ValueError('identity and capability must have the same consumer id and version')
        self._db.execute('INSERT INTO consumers VALUES (?, ?, ?, ?)', (identity.consumer_id,identity.version,identity.consumer_type.value,identity.created_at))
        self._db.execute('INSERT INTO consumer_capabilities VALUES (?, ?, ?, ?, ?)', (capability.consumer_id,capability.version,'\n'.join(item.value for item in capability.allowed_actions),'\n'.join(capability.allowed_packet_versions),capability.purpose)); self._db.commit()
    def get_identity(self, consumer_id: str, version: str) -> ConsumerIdentity | None:
        row=self._db.execute('SELECT * FROM consumers WHERE consumer_id=? AND version=?',(consumer_id,version)).fetchone()
        return ConsumerIdentity(row['consumer_id'],ConsumerType(row['consumer_type']),row['version'],row['created_at']) if row else None
    def get_capability(self, consumer_id: str, version: str) -> ConsumerCapability | None:
        row=self._db.execute('SELECT * FROM consumer_capabilities WHERE consumer_id=? AND version=?',(consumer_id,version)).fetchone()
        return ConsumerCapability(row['consumer_id'],tuple(ConsumerAction(item) for item in row['actions'].split('\n')),tuple(row['packet_versions'].split('\n')),row['purpose'],row['version']) if row else None

