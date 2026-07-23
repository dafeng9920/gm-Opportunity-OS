"""Append-only result store, separate from Candidate, Evidence, Runtime, and Governance stores."""
from __future__ import annotations
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from .contracts import OpportunityGateAssessment

class GateResultStore:
    def __init__(self, database: Path | str) -> None:
        self._connection = sqlite3.connect(database)
        self._connection.execute("CREATE TABLE IF NOT EXISTS opportunity_gate_results (candidate_id TEXT, gate TEXT, version TEXT, status TEXT, result_json TEXT, created_at TEXT)")
    def append(self, assessment: OpportunityGateAssessment) -> None:
        rows = [(assessment.candidate_id, item.gate, item.version, item.status.value, json.dumps(item.to_dict(), sort_keys=True), datetime.now(UTC).isoformat()) for item in assessment.results]
        self._connection.executemany("INSERT INTO opportunity_gate_results VALUES (?, ?, ?, ?, ?, ?)", rows)
        self._connection.commit()
    def list_for(self, candidate_id: str) -> list[dict[str, object]]:
        rows = self._connection.execute("SELECT result_json FROM opportunity_gate_results WHERE candidate_id = ? ORDER BY rowid", (candidate_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]
