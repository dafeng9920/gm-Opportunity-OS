"""Dedicated Consumer audit persistence; intentionally separate from runtime/audit.py."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from .contracts import ConsumerAction, ConsumerAuditDecision, ConsumerAuditEvent
class ConsumerAuditStore:
    def __init__(self, database: Path | str) -> None:
        self._db=sqlite3.connect(database); self._db.row_factory=sqlite3.Row
        self._db.execute('CREATE TABLE IF NOT EXISTS consumer_audit (consumer_id TEXT, packet_id TEXT, packet_version TEXT, action TEXT, decision TEXT, timestamp TEXT)')
    def append(self,event: ConsumerAuditEvent) -> None:
        self._db.execute('INSERT INTO consumer_audit VALUES (?, ?, ?, ?, ?, ?)',(event.consumer_id,event.packet_id,event.packet_version,event.action.value,event.decision.value,event.timestamp)); self._db.commit()
    def list(self) -> list[ConsumerAuditEvent]:
        rows=self._db.execute('SELECT consumer_id, packet_id, packet_version, action, decision, timestamp FROM consumer_audit ORDER BY rowid').fetchall()
        return [ConsumerAuditEvent(row['consumer_id'],row['packet_id'],row['packet_version'],ConsumerAction(row['action']),ConsumerAuditDecision(row['decision']),row['timestamp']) for row in rows]
