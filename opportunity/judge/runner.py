"""Read-only validation boundary for an Opportunity Judge implementation."""
from __future__ import annotations
from typing import Protocol
from .contracts import JudgeAssessment, JudgeInput
class OpportunityJudge(Protocol):
    def assess(self, packet: JudgeInput) -> JudgeAssessment: ...
class OpportunityJudgeRunner:
    def assess(self, judge: OpportunityJudge, packet: JudgeInput) -> JudgeAssessment:
        result = judge.assess(packet)
        if not isinstance(result, JudgeAssessment):
            raise ValueError("judge returned an invalid assessment contract")
        if result.candidate_id != packet.candidate.id:
            raise ValueError("assessment candidate id does not match input")
        if not set(result.evidence_refs).issubset({item.id for item in packet.evidence}):
            raise ValueError("assessment references evidence outside the supplied packet")
        allowed_gates = {f"{item.gate}@{item.version}" for item in packet.gate_results}
        if not set(result.gate_refs).issubset(allowed_gates):
            raise ValueError("assessment references gates outside the supplied packet")
        return result
