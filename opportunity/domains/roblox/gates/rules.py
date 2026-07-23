"""Roblox rules use generic GateResult contracts and never acquire data."""
from __future__ import annotations
from opportunity.gates.contracts import GateStatus, OpportunityGateResult, RuleResult
from ..schemas import RobloxOpportunityCandidate

WEAK_SERP_TYPES = frozenset({"Weak Page", "Reddit", "YouTube"})
CONTENT_TYPES = frozenset({"codes", "wiki", "characters", "tier list", "values", "calculator", "guides", "updates"})
MONETIZATION_TYPES = frozenset({"ads", "affiliate", "tool opportunity", "repeat traffic"})

def _result(candidate: RobloxOpportunityCandidate, gate: str, status: GateStatus, rule: str, observed: object, expected: object) -> OpportunityGateResult:
    return OpportunityGateResult(candidate.candidate_id, gate, "roblox-0.1", status, candidate.evidence_refs, (RuleResult(rule, status, observed, expected),))
def search_demand(candidate: RobloxOpportunityCandidate) -> OpportunityGateResult:
    growth = candidate.trend_signals.get("growth")
    intent = candidate.keyword_metrics.get("search_intent")
    if growth is None or intent is None: return _result(candidate, "roblox.search_demand", GateStatus.UNKNOWN, "trend_growth_required", growth, True)
    return _result(candidate, "roblox.search_demand", GateStatus.PASS if growth is True and bool(intent) else GateStatus.FAIL, "trend_growth_required", growth, True)
def serp_competition(candidate: RobloxOpportunityCandidate) -> OpportunityGateResult:
    if not candidate.serp_snapshot: return _result(candidate, "roblox.serp_competition", GateStatus.UNKNOWN, "weak_result_present", (), tuple(WEAK_SERP_TYPES))
    weak = sorted(WEAK_SERP_TYPES.intersection(candidate.serp_snapshot))
    return _result(candidate, "roblox.serp_competition", GateStatus.PASS if weak else GateStatus.FAIL, "weak_result_present", weak, tuple(WEAK_SERP_TYPES))
def content_expansion(candidate: RobloxOpportunityCandidate) -> OpportunityGateResult:
    if not candidate.content_opportunities: return _result(candidate, "roblox.content_expansion", GateStatus.UNKNOWN, "content_matrix", (), 3)
    recognized = CONTENT_TYPES.intersection(candidate.content_opportunities)
    return _result(candidate, "roblox.content_expansion", GateStatus.PASS if len(recognized) >= 3 else GateStatus.FAIL, "content_matrix", sorted(recognized), 3)
def data_availability(candidate: RobloxOpportunityCandidate) -> OpportunityGateResult:
    if not candidate.available_sources: return _result(candidate, "roblox.data_availability", GateStatus.UNKNOWN, "maintainable_sources", (), ("official data", "community wiki"))
    available = set(candidate.available_sources)
    passed = "official data" in available and bool(available.intersection({"community wiki", "update logs", "API", "public sources"}))
    return _result(candidate, "roblox.data_availability", GateStatus.PASS if passed else GateStatus.FAIL, "maintainable_sources", sorted(available), ("official data", "community wiki"))
def monetization(candidate: RobloxOpportunityCandidate) -> OpportunityGateResult:
    if not candidate.monetization_options: return _result(candidate, "roblox.monetization", GateStatus.UNKNOWN, "monetization_path", (), tuple(MONETIZATION_TYPES))
    paths = MONETIZATION_TYPES.intersection(candidate.monetization_options)
    return _result(candidate, "roblox.monetization", GateStatus.PASS if paths else GateStatus.FAIL, "monetization_path", sorted(paths), tuple(MONETIZATION_TYPES))
