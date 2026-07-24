"""Resolve Candidate-owned evidence and only quality-accepted Gate Facts."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from candidates.evidence_validator import EvidenceReferenceValidator
from core.schemas import CandidatePacket

from .contracts import EvaluationContext

if TYPE_CHECKING:
    from opportunity.fact_quality.contracts import AcceptedFact


class AcceptedGateFactLookup(Protocol):
    """Evaluation's sole fact source: facts accepted by the quality boundary."""

    def list_accepted_for_evidence_ids(
        self, evidence_ids: tuple[str, ...]
    ) -> tuple[AcceptedFact, ...]: ...


class EvidenceResolver:
    """Build evaluation context from Candidate evidence and accepted facts only."""

    def __init__(
        self, validator: EvidenceReferenceValidator, facts: AcceptedGateFactLookup
    ) -> None:
        if not callable(getattr(facts, "list_accepted_for_evidence_ids", None)):
            raise TypeError("Evaluation requires AcceptedFact lookup")
        self._validator = validator
        self._facts = facts

    def resolve(
        self,
        candidate: CandidatePacket,
        domain: str,
        evidence_ids: tuple[str, ...] | None = None,
    ) -> EvaluationContext:
        from opportunity.fact_quality.contracts import AcceptedFact

        selected = evidence_ids if evidence_ids is not None else candidate.evidence_ids
        if set(selected) != set(candidate.evidence_ids) or len(selected) != len(
            candidate.evidence_ids
        ):
            raise ValueError(
                "evaluation evidence must exactly match candidate evidence references"
            )
        self._validator.validate(selected)
        accepted = self._facts.list_accepted_for_evidence_ids(tuple(selected))
        if any(not isinstance(item, AcceptedFact) for item in accepted):
            raise TypeError("Evaluation requires AcceptedFact")
        facts = tuple(item.fact for item in accepted)
        if any(not set(fact.evidence_ids).issubset(selected) for fact in facts):
            raise ValueError("accepted gate fact evidence is outside candidate evidence")
        return EvaluationContext(candidate.id, domain, facts, tuple(selected))