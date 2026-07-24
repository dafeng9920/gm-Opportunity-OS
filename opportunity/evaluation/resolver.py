"""Resolve Candidate-owned evidence and only governed, persisted Gate Facts."""
from __future__ import annotations

from typing import Protocol

from candidates.evidence_validator import EvidenceReferenceValidator
from core.schemas import CandidatePacket

from .contracts import EvaluationContext, EvaluationFact


class GateFactLookup(Protocol):
    def list_for_evidence_ids(self, evidence_ids: tuple[str, ...]) -> tuple[EvaluationFact, ...]: ...


class EvidenceResolver:
    """No collector metadata can enter Gate evaluation; facts must come from the Fact production boundary."""

    def __init__(self, validator: EvidenceReferenceValidator, facts: GateFactLookup) -> None:
        self._validator = validator
        self._facts = facts

    def resolve(self, candidate: CandidatePacket, domain: str, evidence_ids: tuple[str, ...] | None = None) -> EvaluationContext:
        selected = evidence_ids if evidence_ids is not None else candidate.evidence_ids
        if set(selected) != set(candidate.evidence_ids) or len(selected) != len(candidate.evidence_ids):
            raise ValueError("evaluation evidence must exactly match candidate evidence references")
        self._validator.validate(selected)
        facts = self._facts.list_for_evidence_ids(tuple(selected))
        if any(not set(fact.evidence_ids).issubset(selected) for fact in facts):
            raise ValueError("produced gate fact evidence is outside candidate evidence")
        return EvaluationContext(candidate.id, domain, facts, tuple(selected))