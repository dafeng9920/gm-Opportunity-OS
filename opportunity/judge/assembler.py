"""Assemble trusted JudgeInput only from one Evidence-backed CandidateEvaluationResult."""

from __future__ import annotations

from candidates.evidence_validator import EvidenceReferenceValidator
from candidates.repository import CandidateRepository
from opportunity.evaluation.contracts import (
    CandidateEvaluationResult,
    EvaluationContext,
    FactVerification,
)

from .contracts import JudgeInput


class JudgeInputAssembler:
    """Validates Candidate, Evidence, Context, and Gate lineage without executing a Judge."""

    def __init__(
        self,
        candidates: CandidateRepository,
        evidence: EvidenceReferenceValidator,
    ) -> None:
        self._candidates = candidates
        self._evidence = evidence

    def assemble(self, result: CandidateEvaluationResult) -> JudgeInput:
        if not isinstance(result, CandidateEvaluationResult):
            raise ValueError("judge input requires a candidate evaluation result")
        context = result.context
        if not isinstance(context, EvaluationContext):
            raise ValueError("candidate evaluation result requires an evaluation context")
        if result.candidate_id != context.candidate_id:
            raise ValueError("evaluation result candidate does not match context")
        candidate = self._candidates.get(result.candidate_id)
        if candidate is None:
            raise KeyError("evaluation candidate not found")
        if candidate.id != context.candidate_id:
            raise ValueError("persisted candidate does not match evaluation context")
        if set(candidate.evidence_ids) != set(context.evidence_refs):
            raise ValueError("candidate evidence does not match evaluation context")
        evidence_items = self._evidence.validate(candidate.evidence_ids)
        if {item.id for item in evidence_items} != set(context.evidence_refs):
            raise ValueError("resolved evidence does not match evaluation context")
        self._validate_context_lineage(context, result)
        self._validate_gate_lineage(result, context, candidate.id)
        return JudgeInput(candidate, evidence_items, result.assessment.results)

    @staticmethod
    def _validate_context_lineage(context: EvaluationContext, result: CandidateEvaluationResult) -> None:
        facts = {fact.fact_id: fact for fact in context.facts}
        for fact in facts.values():
            if fact.verification is not FactVerification.EVIDENCE_BACKED:
                raise ValueError("judge input cannot use unverified evaluation facts")
            if not set(fact.evidence_ids).issubset(context.evidence_refs):
                raise ValueError("evaluation fact evidence is outside context")
        for field in result.gate_input.fields:
            fact = facts.get(field.fact_id)
            if fact is None:
                raise ValueError("gate input field has no evaluation fact")
            if field.value != fact.value or field.evidence_ids != fact.evidence_ids:
                raise ValueError("gate input field does not match evaluation fact lineage")

    @staticmethod
    def _validate_gate_lineage(
        result: CandidateEvaluationResult,
        context: EvaluationContext,
        candidate_id: str,
    ) -> None:
        if result.assessment.candidate_id != candidate_id:
            raise ValueError("gate assessment candidate does not match persisted candidate")
        for gate in result.assessment.results:
            if gate.candidate_id != candidate_id:
                raise ValueError("gate result candidate does not match persisted candidate")
            if not set(gate.evidence_refs).issubset(context.evidence_refs):
                raise ValueError("gate result evidence is outside evaluation context")
