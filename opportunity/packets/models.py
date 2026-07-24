"""Canonical immutable output contract for an evaluated opportunity."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4
from governance.triad.contracts import GateDecision
from opportunity.gates.contracts import GateStatus, OpportunityGateResult
from opportunity.judge.contracts import AssessmentRecommendation, JudgeAssessment

def now() -> str: return datetime.now(UTC).isoformat()
class PacketLifecycle(StrEnum): DRAFT="DRAFT"; ASSEMBLED="ASSEMBLED"; ASSESSED="ASSESSED"; GOVERNANCE_REVIEWED="GOVERNANCE_REVIEWED"; FINALIZED="FINALIZED"
class NextAction(StrEnum): WAIT="WAIT"; COLLECT_MORE_DATA="COLLECT_MORE_DATA"; REQUEST_REVIEW="REQUEST_REVIEW"; READY_FOR_BUILD_GATE="READY_FOR_BUILD_GATE"
@dataclass(frozen=True, slots=True)
class PacketEvidenceReference:
    evidence_id: str
    source: str
    timestamp: str
@dataclass(frozen=True, slots=True)
class GovernanceSnapshot:
    status: str
    decision: GateDecision | None
    audit_refs: tuple[str, ...]
    decision_artifact_id: str = ""
@dataclass(frozen=True, slots=True)
class OpportunityPacket:
    opportunity_id: str
    domain: str
    created_at: str
    version: str
    signals: tuple[str, ...]
    sources: tuple[str, ...]
    discovery_time: str
    evidence_refs: tuple[PacketEvidenceReference, ...]
    candidate_id: str
    candidate_type: str
    entity: str
    gates: tuple[OpportunityGateResult, ...]
    judge: JudgeAssessment | None
    governance: GovernanceSnapshot
    next_action: NextAction
    def __post_init__(self) -> None:
        if not self.opportunity_id or not self.domain or not self.version or not self.candidate_id: raise ValueError("packet identity is required")
        if not self.evidence_refs: raise ValueError("packet requires evidence references")
        if {item.evidence_id for item in self.evidence_refs} != {ref for gate in self.gates for ref in gate.evidence_refs}: raise ValueError("packet evidence must match gate references")
        if self.judge and self.judge.candidate_id != self.candidate_id: raise ValueError("judge assessment must belong to the packet candidate")
    @classmethod
    def new_id(cls) -> str: return str(uuid4())
