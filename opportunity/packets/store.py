"""Append-only packet history; finalized versions are never overwritten."""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from .models import OpportunityPacket, PacketLifecycle
from .serializer import OpportunityPacketSerializer
@dataclass(frozen=True, slots=True)
class PacketStoredRecord:
    opportunity_id: str
    version: str
    lifecycle: PacketLifecycle
    payload: str
TRANSITIONS = {PacketLifecycle.DRAFT:{PacketLifecycle.ASSEMBLED}, PacketLifecycle.ASSEMBLED:{PacketLifecycle.ASSESSED}, PacketLifecycle.ASSESSED:{PacketLifecycle.GOVERNANCE_REVIEWED}, PacketLifecycle.GOVERNANCE_REVIEWED:{PacketLifecycle.FINALIZED}, PacketLifecycle.FINALIZED:set()}
class OpportunityPacketStore:
    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database); self._db.execute('CREATE TABLE IF NOT EXISTS opportunity_packets (opportunity_id TEXT, version TEXT, lifecycle TEXT, payload TEXT, PRIMARY KEY(opportunity_id, version))')
    def create(self, packet: OpportunityPacket) -> None:
        self._db.execute('INSERT INTO opportunity_packets VALUES (?, ?, ?, ?)', (packet.opportunity_id, packet.version, PacketLifecycle.DRAFT.value, OpportunityPacketSerializer().to_json(packet))); self._db.commit()
    def advance(self, opportunity_id: str, version: str, lifecycle: PacketLifecycle) -> None:
        row = self._db.execute('SELECT lifecycle FROM opportunity_packets WHERE opportunity_id=? AND version=?', (opportunity_id, version)).fetchone()
        if not row: raise KeyError('packet version not found')
        current = PacketLifecycle(row[0])
        if lifecycle not in TRANSITIONS[current]: raise ValueError('illegal packet lifecycle transition')
        self._db.execute('UPDATE opportunity_packets SET lifecycle=? WHERE opportunity_id=? AND version=?', (lifecycle.value, opportunity_id, version)); self._db.commit()
    def get(self, opportunity_id: str, version: str) -> PacketStoredRecord | None:
        row = self._db.execute('SELECT opportunity_id, version, lifecycle, payload FROM opportunity_packets WHERE opportunity_id=? AND version=?', (opportunity_id, version)).fetchone()
        return PacketStoredRecord(row[0], row[1], PacketLifecycle(row[2]), row[3]) if row else None
    def query(self, *, opportunity_id: str = '', version: str = '', domain: str = '', lifecycle: PacketLifecycle | None = None, limit: int = 20) -> tuple[PacketStoredRecord, ...]:
        clauses, values = [], []
        if opportunity_id: clauses.append('opportunity_id=?'); values.append(opportunity_id)
        if version: clauses.append('version=?'); values.append(version)
        if lifecycle: clauses.append('lifecycle=?'); values.append(lifecycle.value)
        if domain: clauses.append("json_extract(payload, '$.domain')=?"); values.append(domain)
        where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
        rows = self._db.execute('SELECT opportunity_id, version, lifecycle, payload FROM opportunity_packets' + where + ' ORDER BY opportunity_id, version LIMIT ?', tuple(values + [limit])).fetchall()
        return tuple(PacketStoredRecord(row[0], row[1], PacketLifecycle(row[2]), row[3]) for row in rows)
    def lifecycle(self, opportunity_id: str, version: str) -> PacketLifecycle:
        row = self._db.execute('SELECT lifecycle FROM opportunity_packets WHERE opportunity_id=? AND version=?', (opportunity_id, version)).fetchone()
        if not row: raise KeyError('packet version not found')
        return PacketLifecycle(row[0])

