"""Composes the existing generic Gate Engine with Roblox-specific rules; does not duplicate it."""
from __future__ import annotations
from core.schemas import CandidatePacket
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus
from .gates import content_expansion, data_availability, monetization, search_demand, serp_competition
from .schemas import RobloxOpportunityAssessment, RobloxOpportunityCandidate
class RobloxOpportunityEvaluator:
    def __init__(self, generic_engine: OpportunityGateEngine | None = None) -> None:
        self._generic_engine = generic_engine or OpportunityGateEngine()
    def assess(self, candidate: CandidatePacket, roblox: RobloxOpportunityCandidate) -> RobloxOpportunityAssessment:
        if candidate.id != roblox.candidate_id: raise ValueError("Roblox candidate must match Candidate Packet")
        if set(candidate.evidence_ids) != set(roblox.evidence_refs): raise ValueError("Roblox evidence refs must match Candidate Packet")
        generic = self._generic_engine.assess(candidate, {
            "trend_up": roblox.trend_signals.get("growth"),
            "keyword_difficulty": roblox.keyword_metrics.get("keyword_difficulty"),
            "long_tail_count": roblox.keyword_metrics.get("long_tail_count"),
            "available_sources": tuple("official" if item == "official data" else "community" if item == "community wiki" else item for item in roblox.available_sources),
            "monetization_path": bool(roblox.monetization_options),
        }).results
        domain = (search_demand(roblox), serp_competition(roblox), content_expansion(roblox), data_availability(roblox), monetization(roblox))
        all_results = generic + domain
        unknowns = tuple(item.gate for item in all_results if item.status is GateStatus.UNKNOWN)
        risks = tuple(item.gate for item in all_results if item.status in {GateStatus.FAIL, GateStatus.BLOCKED})
        return RobloxOpportunityAssessment("roblox", candidate.id, all_results, candidate.evidence_ids, unknowns, risks)
