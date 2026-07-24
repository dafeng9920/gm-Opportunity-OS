"""Validated assembly of governance tasks from persisted assessment assets."""

from __future__ import annotations

from types import MappingProxyType

from candidates.evidence_validator import EvidenceReferenceValidator
from candidates.repository import CandidateRepository
from opportunity.assessments import AssessmentRecordSource, JudgeAssessmentStore

from .contracts import GovernanceTask


class GovernanceTaskAssembler:
    """Creates admission tasks from a verified assessment asset; it never dispatches Triad."""

    def __init__(
        self,
        assessment_store: JudgeAssessmentStore,
        candidate_repository: CandidateRepository,
        evidence_validator: EvidenceReferenceValidator,
    ) -> None:
        self._assessment_store = assessment_store
        self._candidate_repository = candidate_repository
        self._evidence_validator = evidence_validator

    def assemble(
        self,
        assessment_id: str,
        *,
        task_id: str,
        objective: str = "govern opportunity admission",
        expected_output: str = "gate decision",
        test_mode: bool = False,
    ) -> GovernanceTask:
        if not isinstance(assessment_id, str) or not assessment_id.strip():
            raise ValueError("assessment id is required")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("governance task id is required")

        record = self._assessment_store.get(assessment_id)
        if record is None:
            raise KeyError(f"assessment record not found: {assessment_id}")
        if record.source is AssessmentRecordSource.STATIC_TEST_ONLY and not test_mode:
            raise PermissionError("static-only assessment records require explicit test mode")

        candidate = self._candidate_repository.get(record.candidate_id)
        if candidate is None:
            raise KeyError(f"candidate not found for assessment: {record.candidate_id}")
        if tuple(candidate.evidence_ids) != record.evidence_refs:
            raise ValueError("assessment evidence lineage does not match candidate")
        self._evidence_validator.validate(tuple(candidate.evidence_ids))

        if record.assessment.candidate_id != candidate.id:
            raise ValueError("assessment payload candidate does not match candidate asset")
        if not record.gate_refs:
            raise ValueError("assessment record requires gate references")
        if not set(record.assessment.evidence_refs).issubset(record.evidence_refs):
            raise ValueError("assessment payload evidence is outside assessment lineage")
        if not set(record.assessment.gate_refs).issubset(record.gate_refs):
            raise ValueError("assessment payload gates are outside assessment lineage")

        return GovernanceTask(
            id=task_id,
            objective=objective,
            input_refs=(record.assessment_id,),
            expected_output=expected_output,
            metadata=MappingProxyType({
                "assessment_id": record.assessment_id,
                "assessment_record_version": record.record_version,
                "judge_input_hash": record.judge_input_hash,
                "assessment_source": record.source.value,
            }),
            candidate_id=candidate.id,
        )