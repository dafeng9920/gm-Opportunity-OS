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
    LongTailCountProducer,
    MeasurementArtifact,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus


class LongTailCountProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'long-tail-count-{self._testMethodName}.db'
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.items = tuple(f'Grow a Garden guide {index}' for index in range(1, 13))
        self.evidence = self._corpus_evidence(self.items, len(self.items))
        self.ledger.append(self.evidence)
        self.candidate = CandidatePacket(
            'Grow a Garden', 'recorded keyword corpus', (self.evidence.id,), 'evidence-ledger', 0.5
        )
        self.producer = LongTailCountProducer(self.ledger)
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
            'long-tail-count-quality', 'long_tail_count', '0.1',
            ('query_family', 'source', 'method', 'captured_at'),
            ('topic_scope', 'source_reference', 'candidate_items', 'qualified_items', 'count_rule', 'calculated_count'),
            1, ('reproducible-qualified-count',), '0.1',
        )

    @staticmethod
    def _corpus_evidence(items, result, metadata=None) -> EvidenceObject:
        raw_reference = 'https://example.test/keyword-corpus/grow-a-garden'
        data = {
            'long_tail_measurement': {
                'source_reference': raw_reference,
                'topic_scope': 'Grow a Garden',
                'candidate_items': items,
                'count_rule': 'qualified_long_tail_v1',
                'result': result,
            },
        }
        if metadata is not None:
            data = metadata
        return EvidenceObject('keyword-corpus', 'keyword-corpus', raw_reference, metadata=data)

    def _request(self, evidence_id=None) -> FactProductionRequest:
        return FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'long_tail_count', '0.1', (evidence_id or self.evidence.id,),
        )

    def test_qualified_items_produce_accepted_fact_and_content_gate_pass(self) -> None:
        request = self._request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        assessment, accepted = self.quality.assess(produced, artifact)

        self.assertEqual(artifact.output_value, 12)
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            self.candidate, 'content_expansion', {'long_tail_count': accepted.fact.value}
        )
        self.assertEqual(gate.status, GateStatus.PASS)

    def test_count_below_threshold_is_a_fact_but_content_gate_fails(self) -> None:
        items = ('Grow a Garden codes', 'Grow a Garden pets', 'Grow a Garden seeds')
        evidence = self._corpus_evidence(items, 3)
        self.ledger.append(evidence)
        request = self._request(evidence.id)
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        _, accepted = self.quality.assess(produced, artifact)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            CandidatePacket('Limited', 'recorded keyword corpus', (evidence.id,), 'evidence-ledger', 0.5),
            'content_expansion', {'long_tail_count': accepted.fact.value},
        )
        self.assertEqual(gate.status, GateStatus.FAIL)

    def test_absent_long_tail_fact_leaves_content_gate_unknown(self) -> None:
        gate = OpportunityGateEngine().evaluate(self.candidate, 'content_expansion', {})
        self.assertEqual(gate.status, GateStatus.UNKNOWN)

    def test_mismatched_candidate_item_count_is_rejected_before_fact_production(self) -> None:
        items = ('Grow a Garden codes', 'Grow a Garden pets', 'Grow a Garden seeds')
        evidence = self._corpus_evidence(items, 10)
        self.ledger.append(evidence)
        with self.assertRaisesRegex(ValueError, 'result does not match'):
            self.producer.measure(self._request(evidence.id))

    def test_missing_measurement_cannot_produce_long_tail_fact(self) -> None:
        evidence = self._corpus_evidence((), 0, {})
        self.ledger.append(evidence)
        with self.assertRaisesRegex(ValueError, 'missing measurement'):
            self.producer.measure(self._request(evidence.id))

    def test_missing_evidence_provenance_cannot_become_accepted_fact(self) -> None:
        request = self._request()
        artifact = MeasurementArtifact(
            request.request_id, request.producer_id, request.producer_version,
            'long_tail_count', '0.1', request.evidence_ids,
            self.producer.measurement_method,
            {
                'topic_scope': 'grow a garden',
                'source_reference': self.evidence.raw_reference,
                'candidate_items': self.items,
                'qualified_items': self.items,
                'count_rule': 'qualified_long_tail_v1',
                'calculated_count': 12,
            },
            12,
            {'query_family': 'Grow a Garden'},
        )
        with self.assertRaisesRegex(ValueError, 'provenance is missing: source'):
            self.production.produce(request, artifact)

    def test_long_tail_producer_has_no_quality_agent_or_runtime_dependency(self) -> None:
        import ast
        for path in ('opportunity/facts/long_tail.py', 'opportunity/facts/long_tail_producer.py'):
            tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
            imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ('opportunity.fact_quality', 'AcceptedFact', 'crawlers', 'adapters', 'agents', 'runtime', 'governance', 'opportunity.judge'):
                self.assertNotIn(forbidden, imports)