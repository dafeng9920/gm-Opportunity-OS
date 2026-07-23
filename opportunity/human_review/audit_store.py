"""Dedicated persisted audit trail for Human Review runtime actions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .runtime_contracts import HumanReviewAuditAction, HumanReviewAuditEvent


class HumanReviewAuditStore:
    """Review-action audit separate from runtime/audit.py and Consumer READ audit."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS human_review_audit ("
            "review_id TEXT, consumer_id TEXT, packet_id TEXT, action TEXT, decision TEXT, timestamp TEXT)"
        )
        self._db.commit()

    def append(self, event: HumanReviewAuditEvent) -> None:
        self._db.execute(
            "INSERT INTO human_review_audit VALUES (?, ?, ?, ?, ?, ?)",
            (event.review_id, event.consumer_id, event.packet_id, event.action.value, event.decision, event.timestamp),
        )
        self._db.commit()

    def list(self) -> list[HumanReviewAuditEvent]:
        rows = self._db.execute("SELECT * FROM human_review_audit ORDER BY rowid").fetchall()
        return [
            HumanReviewAuditEvent(
                row["review_id"], row["consumer_id"], row["packet_id"],
                HumanReviewAuditAction(row["action"]), row["decision"], row["timestamp"],
            )
            for row in rows
        ]
