import ast
import unittest
from pathlib import Path
from core.schemas import CandidatePacket, EvidenceObject
from opportunity.domains.roblox import RobloxOpportunityCandidate, RobloxOpportunityEvaluator
from opportunity.gates.contracts import GateStatus
from opportunity.judge import JudgeInput

def base(candidate_id: str, evidence_id: str, **changes):
    values = dict(candidate_id=candidate_id, game_name="Fixture Game", experience_id="123", release_date="2026-01-01", search_keywords=("fixture game codes",), trend_signals={"growth": True}, youtube_signals={}, serp_snapshot=("Fandom", "Weak Page"), keyword_metrics={"keyword_difficulty": 20, "long_tail_count": 30, "search_intent": "how to"}, content_opportunities=("codes", "wiki", "characters", "guides"), available_sources=("official data", "community wiki", "update logs"), monetization_options=("ads",), evidence_refs=(evidence_id,))
    values.update(changes)
    return RobloxOpportunityCandidate(**values)
class RobloxPluginTests(unittest.TestCase):
    def setUp(self):
        self.candidate = CandidatePacket("Fixture Game", "signal", ("evidence-1",), "fixture", .5)
        self.evaluator = RobloxOpportunityEvaluator()
    def by_gate(self, assessment): return {item.gate: item.status for item in assessment.gates}
    def test_case_a_high_opportunity_fixture_passes_domain_and_generic_gates(self):
        statuses = self.by_gate(self.evaluator.assess(self.candidate, base(self.candidate.id, "evidence-1")))
        for gate in ("roblox.search_demand", "roblox.serp_competition", "roblox.content_expansion", "roblox.data_availability", "roblox.monetization", "competition"):
            self.assertEqual(statuses[gate], GateStatus.PASS)
    def test_case_b_youtube_attention_but_declining_search_fails_demand(self):
        assessment = self.evaluator.assess(self.candidate, base(self.candidate.id, "evidence-1", trend_signals={"growth": False}, youtube_signals={"views": "high"}))
        self.assertEqual(self.by_gate(assessment)["roblox.search_demand"], GateStatus.FAIL)
    def test_case_c_missing_data_is_unknown_for_every_domain_gate(self):
        assessment = self.evaluator.assess(self.candidate, base(self.candidate.id, "evidence-1", trend_signals={}, serp_snapshot=(), content_opportunities=(), available_sources=(), monetization_options=()))
        statuses = self.by_gate(assessment)
        for gate in ("roblox.search_demand", "roblox.serp_competition", "roblox.content_expansion", "roblox.data_availability", "roblox.monetization"):
            self.assertEqual(statuses[gate], GateStatus.UNKNOWN)
    def test_each_remaining_domain_gate_has_fail_coverage(self):
        assessment = self.evaluator.assess(self.candidate, base(self.candidate.id, "evidence-1", serp_snapshot=("Fandom",), content_opportunities=("codes",), available_sources=("official data",), monetization_options=("sponsorship",)))
        statuses = self.by_gate(assessment)
        for gate in ("roblox.serp_competition", "roblox.content_expansion", "roblox.data_availability", "roblox.monetization"):
            self.assertEqual(statuses[gate], GateStatus.FAIL)
    def test_assessment_gate_results_fit_existing_judge_input_contract(self):
        evidence = EvidenceObject("fixture", "signal", "https://example.test/fixture", id="evidence-1")
        assessment = self.evaluator.assess(self.candidate, base(self.candidate.id, "evidence-1"))
        packet = JudgeInput(self.candidate, (evidence,), assessment.gates)
        self.assertEqual(packet.candidate.id, assessment.candidate_id)
    def test_domain_plugin_has_no_core_writers_or_runtime_dependencies(self):
        tree = ast.parse(Path("opportunity/domains/roblox/evaluator.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("evidence", "runtime", "governance", "agents", "adapters", "crawlers"):
            self.assertNotIn(forbidden, imports)
