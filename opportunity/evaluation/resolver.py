"""Resolve only Candidate-owned Ledger Evidence into traceable evaluation facts."""

from __future__ import annotations

from typing import Any

from candidates.evidence_validator import EvidenceReferenceValidator
from core.schemas import CandidatePacket

from .contracts import EvaluationContext, EvaluationFact, EvaluationFactCategory


class EvidenceResolver:
    """Reads selected Evidence and never accepts caller-supplied Gate facts."""

    def __init__(self, validator: EvidenceReferenceValidator) -> None:
        self._validator = validator

    def resolve(
        self,
        candidate: CandidatePacket,
        domain: str,
        evidence_ids: tuple[str, ...] | None = None,
    ) -> EvaluationContext:
        selected = evidence_ids if evidence_ids is not None else candidate.evidence_ids
        if set(selected) != set(candidate.evidence_ids) or len(selected) != len(candidate.evidence_ids):
            raise ValueError("evaluation evidence must exactly match candidate evidence references")
        evidence_items = self._validator.validate(selected)
        facts: list[EvaluationFact] = []
        for evidence in evidence_items:
            facts.extend(self._facts_from_metadata(evidence.metadata, evidence.id))
        return EvaluationContext(candidate.id, domain, tuple(facts), tuple(selected))

    @staticmethod
    def _facts_from_metadata(metadata: dict[str, Any], evidence_id: str) -> tuple[EvaluationFact, ...]:
        raw_facts = metadata.get("evaluation_facts", ())
        if raw_facts is None:
            raw_facts = ()
        if not isinstance(raw_facts, (list, tuple)):
            raise ValueError("evidence evaluation_facts metadata must be a list")
        facts: list[EvaluationFact] = []
        for raw in raw_facts:
            if not isinstance(raw, dict):
                raise ValueError("evidence evaluation fact metadata must be an object")
            try:
                category = EvaluationFactCategory(raw["category"])
                fact_id = raw["fact_id"]
                value = raw["value"]
            except KeyError as error:
                raise ValueError("evidence evaluation fact requires fact_id, category, and value") from error
            confidence = raw.get("confidence", 1.0)
            facts.append(EvaluationFact(fact_id, category, value, (evidence_id,), confidence))
        return tuple(facts)
