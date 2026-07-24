"""Immutable, versioned asset contracts for future Judge execution output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any
from uuid import uuid4

from opportunity.judge.contracts import JudgeAssessment, JudgeInput


def now() -> str:
    return datetime.now(UTC).isoformat()


class AssessmentRecordSource(StrEnum):
    FUTURE_JUDGE_RUNTIME = "FUTURE_JUDGE_RUNTIME"
    STATIC_TEST_ONLY = "STATIC_TEST_ONLY"


class JudgeInputHasher:
    """Canonical hash for the already validated JudgeInput artifact."""

    @staticmethod
    def hash(judge_input: JudgeInput) -> str:
        value: Any = asdict(judge_input) if is_dataclass(judge_input) else judge_input
        encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class JudgeAssessmentRecord:
    """Append-only execution provenance around an existing JudgeAssessment payload."""

    judge_input_hash: str
    candidate_id: str
    assessment: JudgeAssessment
    evidence_refs: tuple[str, ...]
    gate_refs: tuple[str, ...]
    skill_id: str
    skill_version: str
    runtime_id: str
    runtime_version: str
    audit_refs: tuple[str, ...]
    source: AssessmentRecordSource
    record_version: str
    assessment_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        required = (
            self.assessment_id, self.judge_input_hash, self.candidate_id, self.skill_id,
            self.skill_version, self.runtime_id, self.runtime_version, self.record_version,
            self.created_at,
        )
        if not all(isinstance(item, str) and item.strip() for item in required):
            raise ValueError("assessment record identity is required")
        if not re.fullmatch(r"[0-9a-f]{64}", self.judge_input_hash):
            raise ValueError("judge input hash must be sha256")
        if not re.fullmatch(r"\d+\.\d+", self.record_version):
            raise ValueError("assessment record version must be major.minor")
        if not isinstance(self.assessment, JudgeAssessment):
            raise ValueError("assessment record requires JudgeAssessment payload")
        if not isinstance(self.source, AssessmentRecordSource):
            raise ValueError("assessment record source is invalid")
        for refs, name in ((self.evidence_refs, "evidence"), (self.gate_refs, "gate"), (self.audit_refs, "audit")):
            if not isinstance(refs, tuple) or not all(isinstance(item, str) and item.strip() for item in refs):
                raise ValueError(f"assessment record {name} refs must be immutable strings")
            if len(set(refs)) != len(refs):
                raise ValueError(f"assessment record {name} refs must be unique")
        if self.candidate_id != self.assessment.candidate_id:
            raise ValueError("assessment record candidate must match assessment payload")


class JudgeAssessmentRecordValidator:
    """Validate input/output lineage; it does not execute or interpret a Judge."""

    def validate(self, record: JudgeAssessmentRecord, judge_input: JudgeInput) -> None:
        if record.candidate_id != judge_input.candidate.id:
            raise ValueError("assessment record candidate does not match judge input")
        if record.judge_input_hash != JudgeInputHasher.hash(judge_input):
            raise ValueError("assessment record judge input hash does not match")
        evidence_refs = tuple(item.id for item in judge_input.evidence)
        gate_refs = tuple(f"{item.gate}@{item.version}" for item in judge_input.gate_results)
        if record.evidence_refs != evidence_refs:
            raise ValueError("assessment record evidence refs do not match judge input")
        if record.gate_refs != gate_refs:
            raise ValueError("assessment record gate refs do not match judge input")
        if not set(record.assessment.evidence_refs).issubset(record.evidence_refs):
            raise ValueError("assessment payload evidence refs are outside record lineage")
        if not set(record.assessment.gate_refs).issubset(record.gate_refs):
            raise ValueError("assessment payload gate refs are outside record lineage")
        if record.source is AssessmentRecordSource.STATIC_TEST_ONLY:
            if record.runtime_id != "STATIC_ONLY" or record.runtime_version != "STATIC_ONLY":
                raise ValueError("static assessment records must declare STATIC_ONLY runtime metadata")
        elif record.source is AssessmentRecordSource.FUTURE_JUDGE_RUNTIME:
            if record.runtime_id in {"FUTURE_PENDING", "STATIC_ONLY"} or record.runtime_version in {"FUTURE_PENDING", "STATIC_ONLY"}:
                raise ValueError("future judge runtime records require concrete runtime metadata")
            if not record.audit_refs:
                raise ValueError("future judge runtime records require audit references")
