"""Deterministic mock for contract-placement tests only; no model or runtime call."""
from opportunity.gates.contracts import GateStatus
from .contracts import AssessmentRecommendation, JudgeAssessment, JudgeInput
class DeterministicJudgeAgent:
    def assess(self, packet: JudgeInput) -> JudgeAssessment:
        passes = [item.gate for item in packet.gate_results if item.status is GateStatus.PASS]
        uncertainties = [item.gate for item in packet.gate_results if item.status in {GateStatus.UNKNOWN, GateStatus.BLOCKED}]
        failures = [item.gate for item in packet.gate_results if item.status is GateStatus.FAIL]
        risks = tuple(f"{name} requires interpretation or validation" for name in uncertainties + failures)
        recommendation = AssessmentRecommendation.NO_RECOMMENDATION if failures else AssessmentRecommendation.GATHER_MORE_EVIDENCE if uncertainties else AssessmentRecommendation.SMALL_SCALE_VALIDATION
        return JudgeAssessment(packet.candidate.id, "Deterministic gates passed: " + (", ".join(passes) or "none") + ".", risks, recommendation, tuple(item.id for item in packet.evidence), tuple(f"{item.gate}@{item.version}" for item in packet.gate_results))
