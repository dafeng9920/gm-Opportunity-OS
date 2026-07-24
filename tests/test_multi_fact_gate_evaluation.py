import unittest
from pathlib import Path

from core.schemas import CandidatePacket
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from opportunity.fact_quality import AcceptedFact
from opportunity.facts import ProducedGateFact
from opportunity.gate_evaluation import GateAssessmentStatus, MultiFactGateEvaluator


class _AcceptedLookup:
    def __init__(self, items):
        self.items = tuple(items)

    def list_accepted_for_evidence_ids(self, evidence_ids):
        return self.items


class MultiFactGateEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = CandidatePacket(
            'Fixture Opportunity', 'evidence-backed candidate',
            ('official', 'community', 'trend', 'difficulty', 'content', 'monetization'),
            'fixture', 0.5,
        )
        self.accepted = self._accepted(keyword_difficulty=20)

    @staticmethod
    def _fact(fact_id, category, value, evidence_ids, provenance):
        return EvaluationFact(
            fact_id, category, value, evidence_ids, 1.0,
            FactVerification.EVIDENCE_BACKED, '0.1', provenance,
        )

    def _accepted(self, keyword_difficulty):
        facts = (
            self._fact('available_sources', EvaluationFactCategory.DATA, ('official', 'community'), ('official', 'community'), {
                'source_inventory': 'fixture', 'method': 'fixture-v1', 'captured_at': '2026-01-01',
            }),
            self._fact('trend_up', EvaluationFactCategory.DEMAND, True, ('trend',), {
                'query': 'fixture', 'region': 'US', 'time_window': '7d', 'source': 'fixture', 'method': 'fixture-v1', 'captured_at': '2026-01-01',
            }),
            self._fact('keyword_difficulty', EvaluationFactCategory.COMPETITION, keyword_difficulty, ('difficulty',), {
                'query': 'fixture', 'source': 'fixture', 'method': 'fixture-v1', 'captured_at': '2026-01-01',
            }),
            self._fact('long_tail_count', EvaluationFactCategory.CONTENT, 12, ('content',), {
                'query_family': 'fixture', 'source': 'fixture', 'method': 'fixture-v1', 'captured_at': '2026-01-01',
            }),
            self._fact('monetization_path', EvaluationFactCategory.MONETIZATION, 'ADS', ('monetization',), {
                'path_scope': 'ADS', 'source': 'fixture', 'method': 'fixture-v1', 'captured_at': '2026-01-01',
            }),
        )
        return tuple(AcceptedFact(
            f'accepted-{index}', f'produced-{index}', f'assessment-{index}', '0.1', fact
        ) for index, fact in enumerate(facts, start=1))

    def test_five_accepted_facts_produce_pass_record(self) -> None:
        record = MultiFactGateEvaluator(_AcceptedLookup(self.accepted)).evaluate(self.candidate)
        self.assertEqual(record.overall_status, GateAssessmentStatus.PASS)
        self.assertEqual(len(record.fact_refs), 5)
        self.assertEqual(record.reason_codes, ())

    def test_missing_or_rejected_fact_produces_unknown_not_fail(self) -> None:
        without_trend = tuple(item for item in self.accepted if item.fact.fact_id != 'trend_up')
        record = MultiFactGateEvaluator(_AcceptedLookup(without_trend)).evaluate(self.candidate)
        self.assertEqual(record.overall_status, GateAssessmentStatus.UNKNOWN)
        self.assertIn('missing_fact:trend_up', record.reason_codes)

    def test_present_failing_fact_produces_fail(self) -> None:
        record = MultiFactGateEvaluator(
            _AcceptedLookup(self._accepted(keyword_difficulty=90))
        ).evaluate(self.candidate)
        self.assertEqual(record.overall_status, GateAssessmentStatus.FAIL)
        self.assertIn('gate_failed:competition', record.reason_codes)

    def test_produced_fact_or_non_accepted_lookup_value_is_rejected(self) -> None:
        produced = ProducedGateFact(
            'produced-injection', 'request', 'producer', '0.1', 'artifact', self.accepted[1].fact
        )
        with self.assertRaisesRegex(TypeError, 'requires AcceptedFact'):
            MultiFactGateEvaluator(_AcceptedLookup((produced,))).evaluate(self.candidate)

    def test_evaluator_has_no_judge_triad_packet_agent_or_raw_evidence_dependencies(self) -> None:
        import ast
        tree = ast.parse(Path('opportunity/gate_evaluation/evaluator.py').read_text(encoding='utf-8-sig'))
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ('evidence', 'opportunity.facts', 'opportunity.judge', 'governance', 'opportunity.packets', 'agents', 'runtime', 'skills'):
            self.assertNotIn(forbidden, imports)