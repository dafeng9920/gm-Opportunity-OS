"""Immutable Evidence-backed evaluation contracts; they do not make opportunity decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from opportunity.gates.contracts import OpportunityGateAssessment


def now() -> str:
    return datetime.now(UTC).isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


class EvaluationFactCategory(StrEnum):
    DEMAND = "DEMAND"
    COMPETITION = "COMPETITION"
    CONTENT = "CONTENT"
    DATA = "DATA"
    MONETIZATION = "MONETIZATION"


class FactVerification(StrEnum):
    EVIDENCE_BACKED = "EVIDENCE_BACKED"
    UNVERIFIED_INPUT = "UNVERIFIED_INPUT"


@dataclass(frozen=True, slots=True)
class EvaluationFact:
    fact_id: str
    category: EvaluationFactCategory
    value: Any
    evidence_ids: tuple[str, ...]
    confidence: float
    verification: FactVerification = FactVerification.EVIDENCE_BACKED
    fact_version: str = "0.1"
    provenance: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.fact_id or not self.fact_version or not isinstance(self.evidence_ids, tuple) or not self.evidence_ids or not self.created_at:
            raise ValueError("evaluation fact identity and evidence references are required")
        if not isinstance(self.category, EvaluationFactCategory):
            raise ValueError("evaluation fact category is invalid")
        if not isinstance(self.verification, FactVerification):
            raise ValueError("evaluation fact verification is invalid")
        if not all(isinstance(item, str) and item.strip() for item in self.evidence_ids):
            raise ValueError("evaluation fact evidence ids are invalid")
        if not isinstance(self.confidence, (int, float)) or not 0 <= self.confidence <= 1:
            raise ValueError("evaluation fact confidence must be between 0 and 1")
        if not isinstance(self.provenance, Mapping):
            raise ValueError("evaluation fact provenance must be a mapping")
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "provenance", _freeze(dict(self.provenance)))
        if self.verification is FactVerification.EVIDENCE_BACKED:
            from .fact_validator import GateFactValidator
            GateFactValidator().validate(self)


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    candidate_id: str
    domain: str
    facts: tuple[EvaluationFact, ...]
    evidence_refs: tuple[str, ...]
    contract_version: str = "0.1"
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.domain or not self.contract_version or not self.created_at:
            raise ValueError("evaluation context identity is required")
        if not isinstance(self.facts, tuple) or not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise ValueError("evaluation context facts and evidence references must be immutable tuples")
        if not all(isinstance(item, str) and item.strip() for item in self.evidence_refs):
            raise ValueError("evaluation context evidence references are required")
        allowed = set(self.evidence_refs)
        if any(not set(fact.evidence_ids).issubset(allowed) for fact in self.facts):
            raise ValueError("evaluation facts must reference context evidence")


@dataclass(frozen=True, slots=True)
class GateInputField:
    field: str
    value: Any
    fact_id: str
    evidence_ids: tuple[str, ...]
    fact_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.field or not self.fact_id or not self.fact_version or not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ValueError("gate input field lineage is required")
        object.__setattr__(self, "value", _freeze(self.value))


@dataclass(frozen=True, slots=True)
class GateInputMapping:
    candidate_id: str
    fields: tuple[GateInputField, ...]

    def __post_init__(self) -> None:
        if not self.candidate_id or not isinstance(self.fields, tuple) or not self.fields:
            raise ValueError("gate input mapping identity and fields are required")
        if len({item.field for item in self.fields}) != len(self.fields):
            raise ValueError("gate input fields must be unique")

    def as_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType({item.field: item.value for item in self.fields})


@dataclass(frozen=True, slots=True)
class CandidateEvaluationResult:
    candidate_id: str
    context: EvaluationContext
    gate_input: GateInputMapping
    assessment: OpportunityGateAssessment

    def __post_init__(self) -> None:
        if self.candidate_id != self.context.candidate_id or self.candidate_id != self.gate_input.candidate_id:
            raise ValueError("candidate evaluation artifacts must belong to one candidate")
        if self.assessment.candidate_id != self.candidate_id:
            raise ValueError("gate assessment must belong to evaluation candidate")