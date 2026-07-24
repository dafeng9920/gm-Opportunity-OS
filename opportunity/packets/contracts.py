"""Pure assembly from existing facts; no persistence or system mutation."""
from __future__ import annotations
from core.schemas import CandidatePacket, EvidenceObject
from opportunity.gates.contracts import GateStatus, OpportunityGateResult
from opportunity.judge.contracts import JudgeAssessment
from .models import GovernanceSnapshot, NextAction, OpportunityPacket, PacketEvidenceReference, now
from governance.triad.contracts import GateDecision
def determine_next_action(governance: GovernanceSnapshot, gates: tuple[OpportunityGateResult, ...]) -> NextAction:
    if governance.decision is GateDecision.BLOCK: return NextAction.WAIT
    if governance.decision is GateDecision.REVIEW_REQUIRED or governance.decision is None: return NextAction.REQUEST_REVIEW
    statuses = {item.status for item in gates}
    if GateStatus.UNKNOWN in statuses: return NextAction.COLLECT_MORE_DATA
    if GateStatus.FAIL in statuses or GateStatus.BLOCKED in statuses: return NextAction.WAIT
    return NextAction.READY_FOR_BUILD_GATE
class OpportunityPacketAssembler:
    def assemble(self, *, domain: str, candidate: CandidatePacket, evidence: tuple[EvidenceObject, ...], gates: tuple[OpportunityGateResult, ...], judge: JudgeAssessment | None, governance: GovernanceSnapshot, signals: tuple[str, ...], sources: tuple[str, ...], discovery_time: str, version: str = "0.1") -> OpportunityPacket:
        if {item.id for item in evidence} != set(candidate.evidence_ids): raise ValueError("packet evidence must exactly match candidate references")
        if any(item.candidate_id != candidate.id for item in gates): raise ValueError("packet gates must belong to candidate")
        if not governance.decision_artifact_id: raise ValueError("packet governance snapshot requires decision artifact reference")
        if governance.candidate_id != candidate.id: raise ValueError("packet governance snapshot candidate does not match packet candidate")
        if not governance.assessment_id: raise ValueError("packet governance snapshot requires assessment reference")
        return OpportunityPacket(OpportunityPacket.new_id(), domain, now(), version, signals, sources, discovery_time, tuple(PacketEvidenceReference(item.id, item.source, item.captured_time) for item in evidence), candidate.id, "candidate_packet", candidate.title, gates, judge, governance, determine_next_action(governance, gates))

