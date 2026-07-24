"""Contracts for deterministic aggregation of accepted facts into Gate results."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from opportunity.gates.contracts import OpportunityGateResult


def now() -> str:
    return datetime.now(UTC).isoformat()


class GateAssessmentStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class GatePolicy:
    policy_id: str
    version: str
    required_facts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.policy_id or not self.version or not self.required_facts:
            raise ValueError("gate policy identity and required facts are required")
        if len(set(self.required_facts)) != len(self.required_facts):
            raise ValueError("gate policy required facts must be unique")


@dataclass(frozen=True, slots=True)
class GateAssessmentRecord:
    candidate_id: str
    fact_refs: tuple[str, ...]
    gate_results: tuple[OpportunityGateResult, ...]
    overall_status: GateAssessmentStatus
    reason_codes: tuple[str, ...]
    policy_id: str
    policy_version: str
    assessment_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.assessment_id or not self.created_at:
            raise ValueError("gate assessment record identity is required")
        if len(set(self.fact_refs)) != len(self.fact_refs):
            raise ValueError("gate assessment record fact references must be unique")


DEFAULT_GATE_POLICY = GatePolicy(
    "all-gate-facts", "0.1",
    (
        "available_sources",
        "trend_up",
        "keyword_difficulty",
        "long_tail_count",
        "monetization_path",
    ),
)