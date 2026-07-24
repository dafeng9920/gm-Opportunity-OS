"""Append-only SQLite storage for TriadDecisionArtifact."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from governance.triad.contracts import GateDecision, GateDecisionRecord, Role, RoleArtifact

from .contracts import DecisionArtifactSource, TriadDecisionArtifact


class TriadDecisionStore:
    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS triad_decision_artifacts ("
            "decision_artifact_id TEXT PRIMARY KEY, task_id TEXT, candidate_id TEXT, assessment_id TEXT, "
            "decision TEXT, role_artifacts TEXT, audit_refs TEXT, source TEXT, artifact_version TEXT, created_at TEXT)"
        )
        self._db.commit()

    def append(self, artifact: TriadDecisionArtifact) -> None:
        self._db.execute(
            "INSERT INTO triad_decision_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                artifact.decision_artifact_id, artifact.task_id, artifact.candidate_id, artifact.assessment_id,
                json.dumps({"decision": artifact.decision.decision.value, "rationale": artifact.decision.rationale,
                            "issued_by": artifact.decision.issued_by.value}),
                json.dumps([{"task_id": item.task_id, "role": item.role.value, "summary": item.summary,
                             "formal": item.formal, "input_refs": item.input_refs, "audit_refs": item.audit_refs, "execution_id": item.execution_id, "candidate_id": item.candidate_id, "assessment_id": item.assessment_id} for item in artifact.role_artifacts]),
                json.dumps(artifact.audit_refs), artifact.source.value, artifact.artifact_version, artifact.created_at,
            ),
        )
        self._db.commit()

    def get(self, decision_artifact_id: str) -> TriadDecisionArtifact | None:
        row = self._db.execute(
            "SELECT * FROM triad_decision_artifacts WHERE decision_artifact_id=?", (decision_artifact_id,)
        ).fetchone()
        return self._from_row(row) if row else None

    def list(self) -> list[TriadDecisionArtifact]:
        rows = self._db.execute("SELECT * FROM triad_decision_artifacts ORDER BY rowid").fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TriadDecisionArtifact:
        decision = json.loads(row["decision"])
        artifacts = json.loads(row["role_artifacts"])
        return TriadDecisionArtifact(
            row["task_id"], row["candidate_id"], row["assessment_id"],
            GateDecisionRecord(row["task_id"], GateDecision(decision["decision"]), decision["rationale"], Role(decision["issued_by"])),
            tuple(RoleArtifact(item["task_id"], Role(item["role"]), item["summary"], item["formal"], tuple(item["input_refs"]), tuple(item.get("audit_refs", ())), item.get("execution_id", ""), item.get("candidate_id", ""), item.get("assessment_id", "")) for item in artifacts),
            tuple(json.loads(row["audit_refs"])), DecisionArtifactSource(row["source"]), row["artifact_version"],
            row["decision_artifact_id"], row["created_at"],
        )