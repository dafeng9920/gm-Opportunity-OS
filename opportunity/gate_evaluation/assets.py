"""Append-only Gate Assessment assets between deterministic evaluation and Judge input."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sqlite3
from typing import Protocol
from uuid import uuid4

from candidates.repository import CandidateRepository
from opportunity.fact_quality.contracts import AcceptedFact
from opportunity.gates.contracts import GateStatus, OpportunityGateResult, RuleResult

from .contracts import GateAssessmentRecord, GateAssessmentStatus


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class GateAssessmentAsset:
    """Immutable persisted projection of one deterministic GateAssessmentRecord."""

    candidate_id: str
    gate_assessment_id: str
    fact_refs: tuple[str, ...]
    gate_results: tuple[OpportunityGateResult, ...]
    gate_policy_id: str
    gate_policy_version: str
    assessment_status: GateAssessmentStatus
    reason_codes: tuple[str, ...]
    version: str
    asset_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        required = (self.asset_id, self.candidate_id, self.gate_assessment_id, self.gate_policy_id, self.gate_policy_version, self.version, self.created_at)
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise ValueError("gate assessment asset identity is required")
        if not re.fullmatch(r"\d+\.\d+", self.version):
            raise ValueError("gate assessment asset version must be major.minor")
        if not isinstance(self.assessment_status, GateAssessmentStatus):
            raise ValueError("gate assessment asset status is invalid")
        for refs, name in ((self.fact_refs, "fact"), (self.reason_codes, "reason")):
            if not isinstance(refs, tuple) or not all(isinstance(value, str) and value.strip() for value in refs):
                raise ValueError(f"gate assessment asset {name} refs must be immutable strings")
            if len(set(refs)) != len(refs):
                raise ValueError(f"gate assessment asset {name} refs must be unique")
        if not self.gate_results or any(not isinstance(result, OpportunityGateResult) for result in self.gate_results):
            raise ValueError("gate assessment asset requires gate results")


class AcceptedFactLookup(Protocol):
    def list_accepted_for_evidence_ids(self, evidence_ids: tuple[str, ...]) -> tuple[AcceptedFact, ...]: ...


class GateAssessmentAssetStore:
    """Low-level append-only SQLite storage; authorization belongs to the Writer."""

    def __init__(self, database: Path | str) -> None:
        self._db = sqlite3.connect(database)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS gate_assessment_assets ("
            "asset_id TEXT PRIMARY KEY, candidate_id TEXT, gate_assessment_id TEXT, fact_refs TEXT, "
            "gate_results TEXT, gate_policy_id TEXT, gate_policy_version TEXT, assessment_status TEXT, "
            "reason_codes TEXT, version TEXT, created_at TEXT)"
        )
        self._db.commit()

    def append(self, asset: GateAssessmentAsset) -> None:
        self._db.execute(
            "INSERT INTO gate_assessment_assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (asset.asset_id, asset.candidate_id, asset.gate_assessment_id, json.dumps(asset.fact_refs), json.dumps([item.to_dict() for item in asset.gate_results], sort_keys=True), asset.gate_policy_id, asset.gate_policy_version, asset.assessment_status.value, json.dumps(asset.reason_codes), asset.version, asset.created_at),
        )
        self._db.commit()

    def get(self, asset_id: str) -> GateAssessmentAsset | None:
        row = self._db.execute("SELECT * FROM gate_assessment_assets WHERE asset_id=?", (asset_id,)).fetchone()
        return self._from_row(row) if row else None

    def list(self) -> list[GateAssessmentAsset]:
        rows = self._db.execute("SELECT * FROM gate_assessment_assets ORDER BY rowid").fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _freeze_json(value):
        if isinstance(value, list):
            return tuple(GateAssessmentAssetStore._freeze_json(item) for item in value)
        if isinstance(value, dict):
            return {key: GateAssessmentAssetStore._freeze_json(item) for key, item in value.items()}
        return value

    @staticmethod
    def _from_row(row: sqlite3.Row) -> GateAssessmentAsset:
        results = tuple(
            OpportunityGateResult(value["candidate_id"], value["gate"], value["version"], GateStatus(value["status"]), tuple(value["evidence_refs"]), tuple(RuleResult(rule["rule_id"], GateStatus(rule["status"]), GateAssessmentAssetStore._freeze_json(rule["observed"]), GateAssessmentAssetStore._freeze_json(rule["expected"])) for rule in value["rule_results"]))
            for value in json.loads(row["gate_results"])
        )
        return GateAssessmentAsset(row["candidate_id"], row["gate_assessment_id"], tuple(json.loads(row["fact_refs"])), results, row["gate_policy_id"], row["gate_policy_version"], GateAssessmentStatus(row["assessment_status"]), tuple(json.loads(row["reason_codes"])), row["version"], row["asset_id"], row["created_at"])


class GateAssessmentAssetWriter:
    """The only boundary that turns a runtime Gate Assessment into a persisted asset."""

    def __init__(self, store: GateAssessmentAssetStore, candidates: CandidateRepository, facts: AcceptedFactLookup) -> None:
        if not callable(getattr(facts, "list_accepted_for_evidence_ids", None)):
            raise TypeError("gate assessment asset writer requires AcceptedFact lookup")
        self._store = store
        self._candidates = candidates
        self._facts = facts

    def append(self, record: GateAssessmentRecord, *, version: str = "0.1") -> GateAssessmentAsset:
        if not isinstance(record, GateAssessmentRecord):
            raise TypeError("gate assessment asset requires GateAssessmentRecord")
        candidate = self._candidates.get(record.candidate_id)
        if candidate is None:
            raise KeyError("gate assessment candidate not found")
        self._validate_record(record, candidate.id, candidate.evidence_ids)
        accepted = self._facts.list_accepted_for_evidence_ids(candidate.evidence_ids)
        if any(not isinstance(item, AcceptedFact) for item in accepted):
            raise TypeError("gate assessment asset requires AcceptedFact")
        by_id = {item.accepted_fact_id: item for item in accepted}
        if not set(record.fact_refs).issubset(by_id):
            raise ValueError("gate assessment fact references are outside accepted fact scope")
        if any(not set(by_id[ref].fact.evidence_ids).issubset(candidate.evidence_ids) for ref in record.fact_refs):
            raise ValueError("accepted fact evidence is outside candidate scope")
        asset = GateAssessmentAsset(record.candidate_id, record.assessment_id, record.fact_refs, record.gate_results, record.policy_id, record.policy_version, record.overall_status, record.reason_codes, version)
        self._store.append(asset)
        return asset

    @staticmethod
    def _validate_record(record: GateAssessmentRecord, candidate_id: str, evidence_ids: tuple[str, ...]) -> None:
        if record.candidate_id != candidate_id:
            raise ValueError("gate assessment candidate does not match persisted candidate")
        if not record.gate_results:
            raise ValueError("gate assessment requires gate results")
        if any(item.candidate_id != candidate_id for item in record.gate_results):
            raise ValueError("gate assessment gate result candidate mismatch")
        if any(not set(item.evidence_refs).issubset(evidence_ids) for item in record.gate_results):
            raise ValueError("gate assessment gate evidence is outside candidate scope")
        statuses = {item.status for item in record.gate_results}
        if record.overall_status is GateAssessmentStatus.PASS and statuses != {GateStatus.PASS}:
            raise ValueError("pass gate assessment must contain only passing gates")
        if record.overall_status is GateAssessmentStatus.FAIL and GateStatus.FAIL not in statuses:
            raise ValueError("failed gate assessment requires a failed gate")
        if record.overall_status is GateAssessmentStatus.UNKNOWN:
            has_unknown = GateStatus.UNKNOWN in statuses
            has_missing = any(code.startswith("missing_fact:") for code in record.reason_codes)
            if not has_unknown and not has_missing:
                raise ValueError("unknown gate assessment requires unknown gate or missing fact")



