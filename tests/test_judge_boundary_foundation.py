import unittest
from dataclasses import replace
from pathlib import Path

from candidates import CandidateRepository, EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.assessments import JudgeAssessmentStore, AssessmentRecordWriter, AssessmentRecordSource
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from opportunity.fact_quality import AcceptedFact
from opportunity.facts import ProducedGateFact
from opportunity.gate_evaluation import MultiFactGateEvaluator
from opportunity.judge import GateAssessmentJudgeInputAssembler, StaticJudgeAssessmentRuntime


class _AcceptedLookup:
    def __init__(self, items): self.items = tuple(items)
    def list_accepted_for_evidence_ids(self, evidence_ids): return self.items


class JudgeBoundaryFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'judge-boundary-{self._testMethodName}.db'
        if self.database.exists(): self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = tuple(EvidenceObject('fixture', 'fact', f'https://example.test/{index}') for index in range(6))
        for item in self.evidence: self.ledger.append(item)
        self.candidate = CandidatePacket('Fixture Opportunity', 'evidence-backed candidate', tuple(item.id for item in self.evidence), 'fixture', 0.5)
        self.candidates = CandidateRepository(self.database)
        self.candidates.create(self.candidate)
        self.accepted = self._accepted()
        self.lookup = _AcceptedLookup(self.accepted)
        self.gate_record = MultiFactGateEvaluator(self.lookup).evaluate(self.candidate)
        self.assembler = GateAssessmentJudgeInputAssembler(self.candidates, EvidenceReferenceValidator(self.ledger), self.lookup)

    def _fact(self, fact_id, category, value, evidence_ids, provenance):
        return EvaluationFact(fact_id, category, value, evidence_ids, 1.0, FactVerification.EVIDENCE_BACKED, '0.1', provenance)

    def _accepted(self):
        ids = tuple(item.id for item in self.evidence)
        facts = (
            self._fact('available_sources', EvaluationFactCategory.DATA, ('official', 'community'), ids[:2], {'source_inventory':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
            self._fact('trend_up', EvaluationFactCategory.DEMAND, True, (ids[2],), {'query':'fixture','region':'US','time_window':'7d','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
            self._fact('keyword_difficulty', EvaluationFactCategory.COMPETITION, 20, (ids[3],), {'query':'fixture','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
            self._fact('long_tail_count', EvaluationFactCategory.CONTENT, 12, (ids[4],), {'query_family':'fixture','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
            self._fact('monetization_path', EvaluationFactCategory.MONETIZATION, 'ADS', (ids[5],), {'path_scope':'ADS','source':'fixture','method':'fixture-v1','captured_at':'2026-01-01'}),
        )
        return tuple(AcceptedFact(f'accepted-{index}', f'produced-{index}', f'quality-{index}', '0.1', fact) for index, fact in enumerate(facts, 1))

    def test_gate_assessment_becomes_scoped_judge_input_and_static_asset(self):
        judge_input = self.assembler.assemble(self.gate_record)
        self.assertEqual(judge_input.candidate.id, self.candidate.id)
        self.assertEqual(tuple(item.id for item in judge_input.evidence), self.candidate.evidence_ids)
        store = JudgeAssessmentStore(self.database)
        record = StaticJudgeAssessmentRuntime(AssessmentRecordWriter(store)).assess(judge_input)
        self.assertEqual(record.source, AssessmentRecordSource.STATIC_TEST_ONLY)
        self.assertEqual(record.runtime_id, 'STATIC_ONLY')
        self.assertEqual(store.get(record.assessment_id), record)

    def test_out_of_scope_fact_reference_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside accepted fact scope'):
            self.assembler.assemble(replace(self.gate_record, fact_refs=('not-accepted',)))

    def test_produced_fact_cannot_enter_judge_scope(self):
        produced = ProducedGateFact('produced-injection', 'request', 'producer', '0.1', 'artifact', self.accepted[1].fact)
        assembler = GateAssessmentJudgeInputAssembler(self.candidates, EvidenceReferenceValidator(self.ledger), _AcceptedLookup((produced,)))
        with self.assertRaisesRegex(TypeError, 'requires AcceptedFact'):
            assembler.assemble(self.gate_record)

    def test_bridge_and_static_runtime_have_no_llm_agent_or_triad_dependencies(self):
        import ast
        for path in ('opportunity/judge/gate_assembler.py', 'opportunity/judge/static_runtime.py'):
            tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
            imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ('governance', 'agents', 'openai', 'runtime.manager', 'opportunity.packets', 'skills', 'crawlers', 'adapters'):
                self.assertNotIn(forbidden, imports)