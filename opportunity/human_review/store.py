"""SQLite persistence for Human Review sessions, decisions, records, and history."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from opportunity.consumers.contracts import PacketReference

from .contracts import HumanReviewDecision, HumanReviewDecisionType, HumanReviewRecord
from .runtime_contracts import HumanReviewSession, HumanReviewSessionEvent, HumanReviewSessionStatus, now


class HumanReviewStore:
    """Owns review-domain records only; it never accesses the Opportunity Packet store."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS human_review_sessions ("
            "session_id TEXT PRIMARY KEY, review_id TEXT UNIQUE, consumer_id TEXT, packet_id TEXT, "
            "packet_version TEXT, version TEXT, status TEXT, created_at TEXT, updated_at TEXT)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS human_review_session_events ("
            "session_id TEXT, review_id TEXT, status TEXT, timestamp TEXT)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS human_review_decisions ("
            "review_id TEXT PRIMARY KEY, decision TEXT, reviewer_id TEXT, reason TEXT, timestamp TEXT)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS human_review_records ("
            "review_id TEXT PRIMARY KEY, consumer_id TEXT, packet_id TEXT, packet_version TEXT, "
            "decision TEXT, reviewer_id TEXT, reason TEXT, created_at TEXT)"
        )
        self._db.commit()

    def create_session(self, session: HumanReviewSession) -> None:
        if session.status is not HumanReviewSessionStatus.OPEN:
            raise ValueError("new human review sessions must be OPEN")
        self._db.execute(
            "INSERT INTO human_review_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session.session_id, session.review_id, session.consumer_id, session.packet_reference.packet_id,
                session.packet_reference.packet_version, session.version, session.status.value,
                session.created_at, session.updated_at,
            ),
        )
        self._append_session_event(session, HumanReviewSessionStatus.OPEN, session.created_at)
        self._db.commit()

    def get_session(self, session_id: str) -> HumanReviewSession | None:
        row = self._db.execute("SELECT * FROM human_review_sessions WHERE session_id=?", (session_id,)).fetchone()
        return self._session_from_row(row) if row else None

    def submit_decision(self, session_id: str, decision: HumanReviewDecision, record: HumanReviewRecord) -> HumanReviewSession:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError("human review session not found")
        if session.status is not HumanReviewSessionStatus.OPEN:
            raise ValueError("human review session does not allow submission")
        if decision.review_id != session.review_id or record.review_id != session.review_id:
            raise ValueError("review artifacts do not belong to session")
        if record.consumer_id != session.consumer_id or record.packet_reference != session.packet_reference:
            raise ValueError("review record does not match session")
        self._db.execute(
            "INSERT INTO human_review_decisions VALUES (?, ?, ?, ?, ?)",
            (decision.review_id, decision.decision.value, decision.reviewer_id, decision.reason, decision.timestamp),
        )
        self._db.execute(
            "INSERT INTO human_review_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.review_id, record.consumer_id, record.packet_reference.packet_id,
                record.packet_reference.packet_version, record.decision.value, record.reviewer_id,
                record.reason, record.created_at,
            ),
        )
        updated_at = now()
        self._db.execute(
            "UPDATE human_review_sessions SET status=?, updated_at=? WHERE session_id=?",
            (HumanReviewSessionStatus.SUBMITTED.value, updated_at, session_id),
        )
        submitted = HumanReviewSession(
            session.review_id, session.consumer_id, session.packet_reference, session.version,
            HumanReviewSessionStatus.SUBMITTED, session.session_id, session.created_at, updated_at,
        )
        self._append_session_event(submitted, HumanReviewSessionStatus.SUBMITTED, updated_at)
        self._db.commit()
        return submitted

    def close_session(self, session_id: str) -> HumanReviewSession:
        session = self.get_session(session_id)
        if session is None:
            raise KeyError("human review session not found")
        if session.status is not HumanReviewSessionStatus.SUBMITTED:
            raise ValueError("only submitted human review sessions may close")
        updated_at = now()
        self._db.execute(
            "UPDATE human_review_sessions SET status=?, updated_at=? WHERE session_id=?",
            (HumanReviewSessionStatus.CLOSED.value, updated_at, session_id),
        )
        closed = HumanReviewSession(
            session.review_id, session.consumer_id, session.packet_reference, session.version,
            HumanReviewSessionStatus.CLOSED, session.session_id, session.created_at, updated_at,
        )
        self._append_session_event(closed, HumanReviewSessionStatus.CLOSED, updated_at)
        self._db.commit()
        return closed

    def list_reviews(self) -> list[HumanReviewRecord]:
        rows = self._db.execute("SELECT * FROM human_review_records ORDER BY rowid").fetchall()
        return [
            HumanReviewRecord(
                row["review_id"], row["consumer_id"], PacketReference(row["packet_id"], row["packet_version"]),
                HumanReviewDecisionType(row["decision"]), row["reviewer_id"], row["reason"], row["created_at"],
            )
            for row in rows
        ]

    def list_session_events(self, session_id: str) -> list[HumanReviewSessionEvent]:
        rows = self._db.execute(
            "SELECT session_id, review_id, status, timestamp FROM human_review_session_events "
            "WHERE session_id=? ORDER BY rowid", (session_id,),
        ).fetchall()
        return [
            HumanReviewSessionEvent(row["session_id"], row["review_id"], HumanReviewSessionStatus(row["status"]), row["timestamp"])
            for row in rows
        ]

    def _append_session_event(self, session: HumanReviewSession, status: HumanReviewSessionStatus, timestamp: str) -> None:
        self._db.execute(
            "INSERT INTO human_review_session_events VALUES (?, ?, ?, ?)",
            (session.session_id, session.review_id, status.value, timestamp),
        )

    @staticmethod
    def _session_from_row(row: sqlite3.Row) -> HumanReviewSession:
        return HumanReviewSession(
            row["review_id"], row["consumer_id"], PacketReference(row["packet_id"], row["packet_version"]),
            row["version"], HumanReviewSessionStatus(row["status"]), row["session_id"],
            row["created_at"], row["updated_at"],
        )
