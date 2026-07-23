"""Append-only packet history; finalized versions are never overwritten."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .models import OpportunityPacket, PacketLifecycle
from .serializer import OpportunityPacketSerializer
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
    def lifecycle(self, opportunity_id: str, version: str) -> PacketLifecycle:
        row = self._db.execute('SELECT lifecycle FROM opportunity_packets WHERE opportunity_id=? AND version=?', (opportunity_id, version)).fetchone()
        if not row: raise KeyError('packet version not found')
        return PacketLifecycle(row[0])
