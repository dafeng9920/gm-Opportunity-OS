"""Append-only SQLite storage for JudgeAssessmentRecord assets."""

from __future__ import annotations

from dataclasses import asdict
import json
import sqlite3
from pathlib import Path

from opportunity.judge.contracts import AssessmentRecommendation, JudgeAssessment

from .contracts import AssessmentRecordSource, JudgeAssessmentRecord, JudgeRuntimeSource


class JudgeAssessmentStore:
    """Low-level append-only model; authorization belongs to AssessmentRecordWriter."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS judge_assessment_records ("
            "assessment_id TEXT PRIMARY KEY, judge_input_hash TEXT, candidate_id TEXT, assessment TEXT, "
            "evidence_refs TEXT, gate_refs TEXT, skill_id TEXT, skill_version TEXT, runtime_id TEXT, "
            "runtime_version TEXT, audit_refs TEXT, source TEXT, record_version TEXT, created_at TEXT, input_asset_id TEXT, runtime_source TEXT)"
        )
        self._db.commit()

    def append(self, record: JudgeAssessmentRecord) -> None:
        self._db.execute(
            "INSERT INTO judge_assessment_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.assessment_id, record.judge_input_hash, record.candidate_id,
                json.dumps(self._assessment_to_dict(record.assessment), sort_keys=True),
                json.dumps(record.evidence_refs), json.dumps(record.gate_refs), record.skill_id,
                record.skill_version, record.runtime_id, record.runtime_version,
                json.dumps(record.audit_refs), record.source.value, record.record_version, record.created_at, record.input_asset_id, record.runtime_source.value,
            ),
        )
        self._db.commit()

    def get(self, assessment_id: str) -> JudgeAssessmentRecord | None:
        row = self._db.execute("SELECT * FROM judge_assessment_records WHERE assessment_id=?", (assessment_id,)).fetchone()
        return self._from_row(row) if row else None

    def list(self) -> list[JudgeAssessmentRecord]:
        rows = self._db.execute("SELECT * FROM judge_assessment_records ORDER BY rowid").fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _assessment_to_dict(assessment: JudgeAssessment) -> dict[str, object]:
        data = asdict(assessment)
        data["recommendation"] = assessment.recommendation.value
        return data

    @staticmethod
    def _from_row(row: sqlite3.Row) -> JudgeAssessmentRecord:
        payload = json.loads(row["assessment"])
        assessment = JudgeAssessment(
            payload["candidate_id"], payload["assessment"], tuple(payload["risks"]),
            AssessmentRecommendation(payload["recommendation"]), tuple(payload["evidence_refs"]), tuple(payload["gate_refs"]),
        )
        return JudgeAssessmentRecord(
            row["judge_input_hash"], row["candidate_id"], assessment,
            tuple(json.loads(row["evidence_refs"])), tuple(json.loads(row["gate_refs"])),
            row["skill_id"], row["skill_version"], row["runtime_id"], row["runtime_version"],
            tuple(json.loads(row["audit_refs"])), AssessmentRecordSource(row["source"]),
            row["record_version"], row["assessment_id"], row["created_at"], row["input_asset_id"], JudgeRuntimeSource(row["runtime_source"]),
        )
