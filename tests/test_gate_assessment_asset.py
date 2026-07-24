import sqlite3
import unittest
from dataclasses import replace
from pathlib import Path

from candidates import CandidateRepository
from core.schemas import CandidatePacket
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from opportunity.fact_quality import AcceptedFact
from opportunity.gate_evaluation import GateAssessmentAssetStore, GateAssessmentAssetWriter, GateAssessmentStatus, MultiFactGateEvaluator
from opportunity.gates.contracts import GateStatus
from opportunity.facts import ProducedGateFact


class _AcceptedLookup:
    def __init__(self, items): self.items = tuple(items)
    def list_accepted_for_evidence_ids(self, evidence_ids): return self.items


class GateAssessmentAssetTests(unittest.TestCase):
    def setUp(self):
        self.database = Path('.opportunity-os') / f'gate-assessment-asset-{self._testMethodName}.db'
        if self.database.exists(): self.database.unlink()
        self.candidate = CandidatePacket('Asset fixture', 'signal', ('official', 'community', 'trend', 'difficulty', 'content', 'money'), 'fixture', .5)
        self.candidates = CandidateRepository(self.database)
        self.candidates.create(self.candidate)
        self.accepted = self._accepted()
        self.lookup = _AcceptedLookup(self.accepted)
        self.record = MultiFactGateEvaluator(self.lookup).evaluate(self.candidate)
        self.store = GateAssessmentAssetStore(self.database)
        self.writer = GateAssessmentAssetWriter(self.store, self.candidates, self.lookup)

    def _accepted(self):
        def fact(name, category, value, evidence, provenance):
            return EvaluationFact(name, category, value, evidence, 1.0, FactVerification.EVIDENCE_BACKED, '0.1', provenance)
        definitions = (
            fact('available_sources', EvaluationFactCategory.DATA, ('official', 'community'), ('official', 'community'), {'source_inventory':'fixture','method':'v1','captured_at':'2026'}),
            fact('trend_up', EvaluationFactCategory.DEMAND, True, ('trend',), {'query':'fixture','region':'US','time_window':'7d','source':'fixture','method':'v1','captured_at':'2026'}),
            fact('keyword_difficulty', EvaluationFactCategory.COMPETITION, 20, ('difficulty',), {'query':'fixture','source':'fixture','method':'v1','captured_at':'2026'}),
            fact('long_tail_count', EvaluationFactCategory.CONTENT, 12, ('content',), {'query_family':'fixture','source':'fixture','method':'v1','captured_at':'2026'}),
            fact('monetization_path', EvaluationFactCategory.MONETIZATION, 'ADS', ('money',), {'path_scope':'ADS','source':'fixture','method':'v1','captured_at':'2026'}),
        )
        return tuple(AcceptedFact(f'accepted-{index}', f'produced-{index}', f'quality-{index}', '0.1', value) for index, value in enumerate(definitions, 1))

    def test_valid_record_becomes_immutable_append_only_asset(self):
        asset = self.writer.append(self.record)
        self.assertEqual(asset.assessment_status, GateAssessmentStatus.PASS)
        self.assertEqual(self.store.get(asset.asset_id), asset)
        self.assertEqual(self.store.list(), [asset])
        with self.assertRaises(sqlite3.IntegrityError): self.store.append(asset)
        self.assertFalse(hasattr(self.store, 'update'))
        self.assertFalse(hasattr(self.store, 'delete'))

    def test_rejects_forged_pass_with_failed_gate(self):
        failed = replace(self.record.gate_results[0], status=GateStatus.FAIL)
        forged = replace(self.record, gate_results=(failed,) + self.record.gate_results[1:])
        with self.assertRaisesRegex(ValueError, 'pass gate assessment'):
            self.writer.append(forged)

    def test_rejects_produced_or_unknown_fact_references(self):
        produced = ProducedGateFact('produced', 'request', 'producer', '0.1', 'measurement', self.accepted[0].fact)
        bad_writer = GateAssessmentAssetWriter(self.store, self.candidates, _AcceptedLookup((produced,)))
        with self.assertRaisesRegex(TypeError, 'requires AcceptedFact'):
            bad_writer.append(self.record)
        with self.assertRaisesRegex(ValueError, 'outside accepted fact scope'):
            self.writer.append(replace(self.record, fact_refs=('does-not-exist',)))
