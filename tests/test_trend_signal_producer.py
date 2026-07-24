import unittest
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.fact_quality import (
    FactQualityBoundary,
    FactQualityPolicy,
    FactQualityRegistry,
    FactQualityStore,
    QualityStatus,
)
from opportunity.facts import (
    FactProducerRegistry,
    FactProductionBoundary,
    FactProductionRequest,
    FactProductionStore,
    MeasurementArtifact,
    TrendSignalProducer,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus


class TrendSignalProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'trend-producer-{self._testMethodName}.db'
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = self._trend_evidence((42, 67))
        self.ledger.append(self.evidence)
        self.candidate = CandidatePacket(
            'Grow a Garden', 'recorded trend signal', (self.evidence.id,), 'evidence-ledger', 0.5
        )
        self.producer = TrendSignalProducer(self.ledger)
        producers = FactProducerRegistry()
        producers.register(self.producer.registration())
        self.production = FactProductionBoundary(
            producers, EvidenceReferenceValidator(self.ledger), FactProductionStore(self.database)
        )
        self.quality_store = FactQualityStore(self.database)
        policies = FactQualityRegistry()
        policies.register(self._policy())
        self.quality = FactQualityBoundary(policies, self.quality_store)

    @staticmethod
    def _policy() -> FactQualityPolicy:
        return FactQualityPolicy(
            'trend-quality', 'trend_up', '0.1',
            ('query', 'region', 'time_window', 'source', 'method', 'captured_at'),
            ('source_reference', 'time_window', 'observations', 'comparison_rule', 'calculated_direction'),
            1, ('complete-measurement',), '0.1',
        )

    @staticmethod
    def _trend_evidence(observations, metadata=None) -> EvidenceObject:
        raw_reference = 'https://trends.google.com/trends/explore?geo=US&q=Grow%20a%20Garden'
        data = {
            'query': 'Grow a Garden',
            'region': 'US',
            'trend_measurement': {
                'source_reference': raw_reference,
                'time_window': ('2026-07-01', '2026-07-08'),
                'observations': observations,
                'comparison_rule': 'latest_gt_earliest',
            },
        }
        if metadata is not None:
            data = metadata
        return EvidenceObject('trends.google.com', 'trend-signal', raw_reference, metadata=data)

    def _request(self) -> FactProductionRequest:
        return FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'trend_up', '0.1', (self.evidence.id,),
        )

    def test_recorded_trend_evidence_reaches_accepted_fact_and_demand_gate(self) -> None:
        request = self._request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        assessment, accepted = self.quality.assess(produced, artifact)

        self.assertTrue(artifact.output_value)
        self.assertEqual(artifact.measurements['comparison_rule'], 'latest_gt_earliest')
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            self.candidate, 'demand', {'trend_up': accepted.fact.value}
        )
        self.assertEqual(gate.status, GateStatus.PASS)

    def test_declining_observations_produce_false_fact_and_fail_demand_gate(self) -> None:
        evidence = self._trend_evidence((67, 42))
        self.ledger.append(evidence)
        request = FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'trend_up', '0.1', (evidence.id,),
        )
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        _, accepted = self.quality.assess(produced, artifact)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            CandidatePacket('Declining', 'recorded trend signal', (evidence.id,), 'evidence-ledger', 0.5),
            'demand', {'trend_up': accepted.fact.value},
        )
        self.assertEqual(gate.status, GateStatus.FAIL)

    def test_absent_trend_fact_leaves_demand_gate_unknown(self) -> None:
        gate = OpportunityGateEngine().evaluate(self.candidate, 'demand', {})
        self.assertEqual(gate.status, GateStatus.UNKNOWN)
    def test_missing_measurement_cannot_produce_trend_fact(self) -> None:
        evidence = self._trend_evidence((), {'query': 'Grow a Garden', 'region': 'US'})
        self.ledger.append(evidence)
        request = FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'trend_up', '0.1', (evidence.id,),
        )
        with self.assertRaisesRegex(ValueError, 'missing trend measurement'):
            self.producer.measure(request)

    def test_missing_evidence_provenance_cannot_be_accepted(self) -> None:
        request = self._request()
        artifact = MeasurementArtifact(
            request.request_id, request.producer_id, request.producer_version,
            'trend_up', '0.1', request.evidence_ids,
            self.producer.measurement_method,
            {
                'source_reference': self.evidence.raw_reference,
                'time_window': ('2026-07-01', '2026-07-08'),
                'observations': (42, 67),
                'comparison_rule': 'latest_gt_earliest',
                'calculated_direction': True,
            },
            True,
            {'time_window': ('2026-07-01', '2026-07-08'), 'source': 'trends.google.com'},
        )
        with self.assertRaisesRegex(ValueError, 'provenance is missing: query, region'):
            self.production.produce(request, artifact)

    def test_trend_producer_has_no_accepted_fact_agent_or_runtime_dependency(self) -> None:
        import ast
        for path in ('opportunity/facts/trend.py', 'opportunity/facts/trend_producer.py'):
            tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
            imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ('opportunity.fact_quality', 'AcceptedFact', 'crawlers', 'adapters', 'agents', 'runtime', 'governance', 'opportunity.judge'):
                self.assertNotIn(forbidden, imports)