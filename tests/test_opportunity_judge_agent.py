import ast
import unittest
from pathlib import Path
from core.schemas import CandidatePacket, EvidenceObject
from opportunity.gates import OpportunityGateEngine
from opportunity.judge import AssessmentRecommendation, DeterministicJudgeAgent, JudgeInput, OpportunityJudgeRunner
from opportunity.judge.contracts import JudgeAssessment
class OpportunityJudgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evidence = EvidenceObject("test", "signal", "https://example.test/source")
        self.candidate = CandidatePacket("Example", "signal", (self.evidence.id,), "test", 0.5)
        self.results = OpportunityGateEngine().assess(self.candidate, {"trend_up": True, "keyword_difficulty": 20, "long_tail_count": 20, "available_sources": ("official", "community")}).results
        self.packet = JudgeInput(self.candidate, (self.evidence,), self.results)
    def test_judge_explains_facts_and_marks_unknown_for_followup(self):
        result = OpportunityJudgeRunner().assess(DeterministicJudgeAgent(), self.packet)
        self.assertEqual(result.recommendation, AssessmentRecommendation.GATHER_MORE_EVIDENCE)
        self.assertIn("monetization", " ".join(result.risks))
        self.assertEqual(result.evidence_refs, (self.evidence.id,))
    def test_input_rejects_evidence_not_owned_by_candidate(self):
        with self.assertRaisesRegex(ValueError, "exactly match"):
            JudgeInput(self.candidate, (EvidenceObject("test", "signal", "https://example.test/other"),), self.results)
    def test_runner_rejects_assessment_outside_submitted_evidence(self):
        class BadJudge:
            def assess(self, packet):
                return JudgeAssessment(packet.candidate.id, "x", (), AssessmentRecommendation.NO_RECOMMENDATION, ("other",), ("demand@0.1",))
        with self.assertRaisesRegex(ValueError, "outside"):
            OpportunityJudgeRunner().assess(BadJudge(), self.packet)
    def test_judge_has_no_system_writer_dependencies(self):
        tree = ast.parse(Path("opportunity/judge/runner.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("evidence", "runtime", "governance", "agents", "candidates", "adapters"):
            self.assertNotIn(forbidden, imports)
