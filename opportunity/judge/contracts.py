"""Contracts for interpretation after deterministic gates; no authority to decide."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from core.schemas import CandidatePacket, EvidenceObject
from opportunity.gates.contracts import OpportunityGateResult
class AssessmentRecommendation(StrEnum):
    SMALL_SCALE_VALIDATION = "SMALL_SCALE_VALIDATION"
    GATHER_MORE_EVIDENCE = "GATHER_MORE_EVIDENCE"
    NO_RECOMMENDATION = "NO_RECOMMENDATION"
@dataclass(frozen=True, slots=True)
class JudgeInput:
    candidate: CandidatePacket
    evidence: tuple[EvidenceObject, ...]
    gate_results: tuple[OpportunityGateResult, ...]
    def __post_init__(self) -> None:
        if {item.id for item in self.evidence} != set(self.candidate.evidence_ids):
            raise ValueError("Judge input evidence must exactly match candidate evidence references")
        if not self.gate_results:
            raise ValueError("Judge input requires gate results")
        if any(item.candidate_id != self.candidate.id for item in self.gate_results):
            raise ValueError("gate results must belong to the candidate")
@dataclass(frozen=True, slots=True)
class JudgeAssessment:
    candidate_id: str
    assessment: str
    risks: tuple[str, ...]
    recommendation: AssessmentRecommendation
    evidence_refs: tuple[str, ...]
    gate_refs: tuple[str, ...]
    def __post_init__(self) -> None:
        if not self.candidate_id or not self.assessment:
            raise ValueError("assessment requires candidate id and explanation")
        if not isinstance(self.recommendation, AssessmentRecommendation):
            raise ValueError("recommendation must be a bounded assessment recommendation")
        if not all(item for item in self.risks + self.evidence_refs + self.gate_refs):
            raise ValueError("assessment references and risks must be non-empty when present")
