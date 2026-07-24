import unittest
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.evaluation import EvidenceResolver
from opportunity.fact_quality import (
    FactQualityBoundary,
    FactQualityPolicy,
    FactQualityRegistry,
    FactQualityStore,
    QualityStatus,
)
from opportunity.facts import (
    FactProducer,
    FactProducerRegistry,
    FactProductionBoundary,
    FactProductionRequest,
    FactProductionStore,
    FactSupport,
    MeasurementArtifact,
)


class _ProducedFactLookup:
    def __init__(self, produced):
        self.produced = produced

    def list_accepted_for_evidence_ids(self, evidence_ids):
        return (self.produced,)


class AcceptedFactGateEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'accepted-fact-gate-{self._testMethodName}.db'
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject('fixture', 'raw', 'https://example.test/source')
        self.ledger.append(self.evidence)
        self.validator = EvidenceReferenceValidator(self.ledger)
        self.candidate = CandidatePacket(
            'Fixture Game', 'signal', (self.evidence.id,), 'fixture', 0.5
        )
        producers = FactProducerRegistry()
        producers.register(FactProducer(
            'trend-producer', '0.1',
            (FactSupport('trend_up', '0.1', ('trend-delta-v1',)),),
        ))
        self.production_store = FactProductionStore(self.database)
        self.producer = FactProductionBoundary(producers, self.validator, self.production_store)

    def _produced(self):
        request = FactProductionRequest(
            'trend-producer', '0.1', 'trend_up', '0.1', (self.evidence.id,)
        )
        artifact = MeasurementArtifact(
            request.request_id, request.producer_id, request.producer_version,
            'trend_up', '0.1', request.evidence_ids, 'trend-delta-v1',
            {'series_points': 2}, True,
            {
                'query': 'fixture', 'region': 'US', 'time_window': '7d',
                'source': 'fixture', 'method': 'trend-delta-v1',
                'captured_at': '2026-01-01T00:00:00+00:00',
            },
        )
        return self.producer.produce(request, artifact), artifact

    @staticmethod
    def _policy(minimum_evidence_count: int) -> FactQualityPolicy:
        return FactQualityPolicy(
            'trend-quality', 'trend_up', '0.1',
            ('query', 'region', 'time_window', 'source', 'method', 'captured_at'),
            ('series_points',), minimum_evidence_count, ('complete',), '0.1',
        )

    def test_runtime_rejects_produced_fact_returned_by_dynamic_lookup(self) -> None:
        produced, _ = self._produced()
        resolver = EvidenceResolver(self.validator, _ProducedFactLookup(produced))
        with self.assertRaisesRegex(TypeError, 'Evaluation requires AcceptedFact'):
            resolver.resolve(self.candidate, 'roblox')

    def test_fact_production_store_cannot_be_used_as_evaluation_lookup(self) -> None:
        with self.assertRaisesRegex(TypeError, 'Evaluation requires AcceptedFact lookup'):
            EvidenceResolver(self.validator, self.production_store)

    def test_quality_accepted_fact_is_consumed_by_evaluation(self) -> None:
        produced, artifact = self._produced()
        quality_store = FactQualityStore(self.database)
        quality_registry = FactQualityRegistry()
        quality_registry.register(self._policy(1))
        assessment, accepted = FactQualityBoundary(quality_registry, quality_store).assess(
            produced, artifact
        )
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        context = EvidenceResolver(self.validator, quality_store).resolve(
            self.candidate, 'roblox'
        )
        self.assertEqual(tuple(item.fact_id for item in context.facts), ('trend_up',))

    def test_rejected_fact_is_not_read_by_evaluation(self) -> None:
        produced, artifact = self._produced()
        quality_store = FactQualityStore(self.database)
        quality_registry = FactQualityRegistry()
        quality_registry.register(self._policy(2))
        assessment, accepted = FactQualityBoundary(quality_registry, quality_store).assess(
            produced, artifact
        )
        self.assertEqual(assessment.status, QualityStatus.FAIL)
        self.assertIsNone(accepted)
        context = EvidenceResolver(self.validator, quality_store).resolve(
            self.candidate, 'roblox'
        )
        self.assertEqual(context.facts, ())
