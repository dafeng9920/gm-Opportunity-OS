"""Assemble JudgeInput only from a persisted, scoped Gate Assessment asset."""
from __future__ import annotations

from typing import Protocol

from candidates.evidence_validator import EvidenceReferenceValidator
from candidates.repository import CandidateRepository
from opportunity.fact_quality.contracts import AcceptedFact
from opportunity.gate_evaluation.assets import GateAssessmentAsset, GateAssessmentAssetStore
from opportunity.gate_evaluation.contracts import GateAssessmentStatus
from opportunity.gates.contracts import GateStatus

from .contracts import JudgeInput


class AcceptedFactLookup(Protocol):
    def list_accepted_for_evidence_ids(self, evidence_ids: tuple[str, ...]) -> tuple[AcceptedFact, ...]: ...


class GateAssessmentJudgeInputAssembler:
    """Converts only persisted accepted-fact Gate Assets into strictly scoped JudgeInput."""

    def __init__(self, candidates: CandidateRepository, evidence: EvidenceReferenceValidator, facts: AcceptedFactLookup, assets: GateAssessmentAssetStore) -> None:
        if not callable(getattr(facts, "list_accepted_for_evidence_ids", None)):
            raise TypeError("judge gate assessment requires AcceptedFact lookup")
        self._candidates = candidates
        self._evidence = evidence
        self._facts = facts
        self._assets = assets

    def assemble(self, asset: GateAssessmentAsset) -> JudgeInput:
        if not isinstance(asset, GateAssessmentAsset):
            raise TypeError("judge input requires GateAssessmentAsset")
        if self._assets.get(asset.asset_id) != asset:
            raise ValueError("judge input requires persisted gate assessment asset")
        candidate = self._candidates.get(asset.candidate_id)
        if candidate is None:
            raise KeyError("gate assessment candidate not found")
        evidence_items = self._evidence.validate(candidate.evidence_ids)
        self._validate_asset(asset, candidate.id, candidate.evidence_ids)
        accepted = self._facts.list_accepted_for_evidence_ids(candidate.evidence_ids)
        if any(not isinstance(item, AcceptedFact) for item in accepted):
            raise TypeError("judge gate assessment requires AcceptedFact")
        accepted_by_id = {item.accepted_fact_id: item for item in accepted}
        if not set(asset.fact_refs).issubset(accepted_by_id):
            raise ValueError("gate assessment fact references are outside accepted fact scope")
        if any(not set(accepted_by_id[fact_id].fact.evidence_ids).issubset(candidate.evidence_ids) for fact_id in asset.fact_refs):
            raise ValueError("accepted fact evidence is outside candidate scope")
        return JudgeInput(candidate, evidence_items, asset.gate_results)

    @staticmethod
    def _validate_asset(asset: GateAssessmentAsset, candidate_id: str, evidence_ids: tuple[str, ...]) -> None:
        if asset.candidate_id != candidate_id:
            raise ValueError("gate assessment candidate does not match persisted candidate")
        if not asset.gate_results:
            raise ValueError("gate assessment requires gate results")
        if any(item.candidate_id != candidate_id for item in asset.gate_results):
            raise ValueError("gate assessment gate result candidate mismatch")
        if any(not set(item.evidence_refs).issubset(evidence_ids) for item in asset.gate_results):
            raise ValueError("gate assessment gate evidence is outside candidate scope")
        statuses = {item.status for item in asset.gate_results}
        if asset.assessment_status is GateAssessmentStatus.PASS and statuses != {GateStatus.PASS}:
            raise ValueError("pass gate assessment must contain only passing gates")
        if asset.assessment_status is GateAssessmentStatus.FAIL and GateStatus.FAIL not in statuses:
            raise ValueError("failed gate assessment requires a failed gate")
        if asset.assessment_status is GateAssessmentStatus.UNKNOWN:
            has_unknown = GateStatus.UNKNOWN in statuses
            has_missing = any(code.startswith("missing_fact:") for code in asset.reason_codes)
            if not has_unknown and not has_missing:
                raise ValueError("unknown gate assessment requires unknown gate or missing fact")
