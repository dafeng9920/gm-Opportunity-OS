import unittest
from pathlib import Path

from candidates import EvidenceReferenceValidator
from core.schemas import EvidenceObject
from evidence import EvidenceLedger
from opportunity.facts import FactProducer, FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, FactSupport, MeasurementArtifact


class FactProductionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.database = Path('.opportunity-os') / f'fact-production-{self._testMethodName}.db'
        if self.database.exists(): self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject('fixture', 'raw', 'https://example.test/raw')
        self.ledger.append(self.evidence)
        self.registry = FactProducerRegistry()
        self.registry.register(FactProducer('trend-producer', '0.1', (FactSupport('trend_up', '0.1', ('trend-delta-v1',)),)))
        self.store = FactProductionStore(self.database)
        self.boundary = FactProductionBoundary(self.registry, EvidenceReferenceValidator(self.ledger), self.store)

    def request(self): return FactProductionRequest('trend-producer', '0.1', 'trend_up', '0.1', (self.evidence.id,))
    def artifact(self, request):
        return MeasurementArtifact(request.request_id, 'trend-producer', '0.1', 'trend_up', '0.1', (self.evidence.id,), 'trend-delta-v1', {'series_points': 2}, True, {'query': 'fixture', 'region': 'US', 'time_window': '7d', 'source': 'fixture', 'method': 'wrong-is-overridden', 'captured_at': 'ignored'})

    def test_registered_producer_persists_validated_fact_with_measurement_lineage(self):
        request = self.request()
        produced = self.boundary.produce(request, self.artifact(request))
        facts = self.store.list_for_evidence_ids((self.evidence.id,))
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].fact_id, 'trend_up')
        self.assertEqual(facts[0].provenance['method'], 'trend-delta-v1')
        self.assertEqual(produced.fact.evidence_ids, (self.evidence.id,))

    def test_rejects_unregistered_producer_method_and_artifact_lineage_mismatch(self):
        request = self.request()
        bad = self.artifact(request)
        object.__setattr__(bad, 'measurement_method', 'unknown')
        with self.assertRaisesRegex(ValueError, 'method'):
            self.boundary.produce(request, bad)
        foreign = FactProductionRequest('missing', '0.1', 'trend_up', '0.1', (self.evidence.id,))
        with self.assertRaisesRegex(KeyError, 'not registered'):
            self.boundary.produce(foreign, self.artifact(foreign))

    def test_production_boundary_has_no_collector_or_runtime_dependencies(self):
        import ast
        tree = ast.parse(Path('opportunity/facts/boundary.py').read_text(encoding='utf-8-sig'))
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ('crawlers', 'adapters', 'intelligence', 'runtime', 'agents', 'governance', 'opportunity.judge'):
            self.assertNotIn(forbidden, imports)