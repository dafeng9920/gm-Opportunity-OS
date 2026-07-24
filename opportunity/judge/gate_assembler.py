"""Assemble JudgeInput only from a scoped multi-fact GateAssessmentRecord."""
from __future__ import annotations

from typing import Protocol

from candidates.evidence_validator import EvidenceReferenceValidator
from candidates.repository import CandidateRepository
from opportunity.fact_quality.contracts import AcceptedFact
from opportunity.gate_evaluation.contracts import GateAssessmentRecord, GateAssessmentStatus
from opportunity.gates.contracts import GateStatus

from .contracts import JudgeInput


class AcceptedFactLookup(Protocol):
    def list_accepted_for_evidence_ids(
        self, evidence_ids: tuple[str, ...]
    ) -> tuple[AcceptedFact, ...]: ...


class GateAssessmentJudgeInputAssembler:
    """Converts an accepted-fact Gate Assessment into a strictly scoped JudgeInput."""

    def __init__(
        self,
        candidates: CandidateRepository,
        evidence: EvidenceReferenceValidator,
        facts: AcceptedFactLookup,
    ) -> None:
        if not callable(getattr(facts, "list_accepted_for_evidence_ids", None)):
            raise TypeError("judge gate assessment requires AcceptedFact lookup")
        self._candidates = candidates
        self._evidence = evidence
        self._facts = facts

    def assemble(self, record: GateAssessmentRecord) -> JudgeInput:
        if not isinstance(record, GateAssessmentRecord):
            raise TypeError("judge input requires GateAssessmentRecord")
        candidate = self._candidates.get(record.candidate_id)
        if candidate is None:
            raise KeyError("gate assessment candidate not found")
        evidence_items = self._evidence.validate(candidate.evidence_ids)
        self._validate_record(record, candidate.id, candidate.evidence_ids)
        accepted = self._facts.list_accepted_for_evidence_ids(candidate.evidence_ids)
        if any(not isinstance(item, AcceptedFact) for item in accepted):
            raise TypeError("judge gate assessment requires AcceptedFact")
        accepted_by_id = {item.accepted_fact_id: item for item in accepted}
        if not set(record.fact_refs).issubset(accepted_by_id):
            raise ValueError("gate assessment fact references are outside accepted fact scope")
        if any(
            not set(accepted_by_id[fact_id].fact.evidence_ids).issubset(candidate.evidence_ids)
            for fact_id in record.fact_refs
        ):
            raise ValueError("accepted fact evidence is outside candidate scope")
        return JudgeInput(candidate, evidence_items, record.gate_results)

    @staticmethod
    def _validate_record(
        record: GateAssessmentRecord,
        candidate_id: str,
        evidence_ids: tuple[str, ...],
    ) -> None:
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