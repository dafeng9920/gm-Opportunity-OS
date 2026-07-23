import ast
import unittest
from pathlib import Path
from core.schemas import CandidatePacket
from opportunity.gates import GateResultStore, GateStatus, OpportunityGateEngine

def candidate() -> CandidatePacket:
    return CandidatePacket("Example", "observed signal", ("evidence-1",), "test", 0.5)

class OpportunityGateEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = OpportunityGateEngine()
        self.candidate = candidate()
    def test_positive_five_gate_assessment_is_pass(self):
        assessment = self.engine.assess(self.candidate, {"trend_up": True, "keyword_difficulty": 20, "long_tail_count": 20, "available_sources": ("official", "community"), "monetization_path": "affiliate"})
        self.assertEqual({result.status for result in assessment.results}, {GateStatus.PASS})
        self.assertEqual({result.version for result in assessment.results}, {"0.1"})
    def test_negative_competition_gate_fails(self):
        self.assertEqual(self.engine.evaluate(self.candidate, "competition", {"keyword_difficulty": 80}).status, GateStatus.FAIL)
    def test_missing_data_is_unknown_and_explicit_block_is_blocked(self):
        self.assertEqual(self.engine.evaluate(self.candidate, "demand", {}).status, GateStatus.UNKNOWN)
        self.assertEqual(self.engine.evaluate(self.candidate, "demand", {"trend_up": True}, frozenset({"demand"})).status, GateStatus.BLOCKED)
    def test_result_store_is_separate_and_candidate_is_unchanged(self):
        path = Path(".opportunity-os") / "gate-test.db"
        if path.exists(): path.unlink()
        before = self.candidate.status
        assessment = self.engine.assess(self.candidate, {"trend_up": True})
        store = GateResultStore(path)
        store.append(assessment)
        self.assertEqual(len(store.list_for(self.candidate.id)), 5)
        self.assertEqual(self.candidate.status, before)
    def test_engine_boundary_imports_only_candidate_contract(self):
        tree = ast.parse(Path("opportunity/gates/engine.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertIn("core.schemas", imports)
        for forbidden in ("evidence", "runtime", "governance", "agents", "candidates"):
            self.assertNotIn(forbidden, imports)
