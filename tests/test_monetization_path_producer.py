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
    MonetizationPathProducer,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus


class MonetizationPathProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'monetization-path-{self._testMethodName}.db'
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = self._path_evidence('ADS', 'PLATFORM_AD_PROGRAM', 'ADS')
        self.ledger.append(self.evidence)
        self.candidate = CandidatePacket(
            'Grow a Garden', 'recorded monetization evidence', (self.evidence.id,), 'evidence-ledger', 0.5
        )
        self.producer = MonetizationPathProducer(self.ledger)
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
            'monetization-path-quality', 'monetization_path', '0.1',
            ('path_scope', 'source', 'method', 'captured_at'),
            ('source_reference', 'path', 'evidence_kind', 'validation_rule', 'calculated_path'),
            1, ('controlled-path-evidence',), '0.1',
        )

    @staticmethod
    def _path_evidence(path, evidence_kind, result, metadata=None) -> EvidenceObject:
        raw_reference = 'https://create.roblox.com/docs/production/monetization'
        data = {
            'monetization_path_measurement': {
                'source_reference': raw_reference,
                'path': path,
                'evidence_kind': evidence_kind,
                'validation_rule': 'recognized_monetization_path_v1',
                'result': result,
            },
        }
        if metadata is not None:
            data = metadata
        return EvidenceObject('create.roblox.com', 'platform-monetization-doc', raw_reference, metadata=data)

    def _request(self, evidence_id=None) -> FactProductionRequest:
        return FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'monetization_path', '0.1', (evidence_id or self.evidence.id,),
        )

    def test_controlled_ads_evidence_produces_accepted_fact_and_monetization_gate_pass(self) -> None:
        request = self._request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        assessment, accepted = self.quality.assess(produced, artifact)

        self.assertEqual(artifact.output_value, 'ADS')
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            self.candidate, 'monetization', {'monetization_path': accepted.fact.value}
        )
        self.assertEqual(gate.status, GateStatus.PASS)

    def test_absent_monetization_fact_leaves_gate_unknown(self) -> None:
        gate = OpportunityGateEngine().evaluate(self.candidate, 'monetization', {})
        self.assertEqual(gate.status, GateStatus.UNKNOWN)

    def test_unknown_path_cannot_become_nonempty_gate_input(self) -> None:
        evidence = self._path_evidence('UNKNOWN', 'PLATFORM_AD_PROGRAM', 'UNKNOWN')
        self.ledger.append(evidence)
        with self.assertRaisesRegex(ValueError, 'invalid controlled values'):
            self.producer.measure(self._request(evidence.id))

    def test_mismatched_controlled_evidence_kind_is_rejected(self) -> None:
        evidence = self._path_evidence('ADS', 'AFFILIATE_PROGRAM', 'ADS')
        self.ledger.append(evidence)
        with self.assertRaisesRegex(ValueError, 'invalid controlled values'):
            self.producer.measure(self._request(evidence.id))

    def test_missing_measurement_cannot_produce_monetization_fact(self) -> None:
        evidence = self._path_evidence('ADS', 'PLATFORM_AD_PROGRAM', 'ADS', {})
        self.ledger.append(evidence)
        with self.assertRaisesRegex(ValueError, 'missing measurement'):
            self.producer.measure(self._request(evidence.id))

    def test_missing_evidence_provenance_cannot_become_accepted_fact(self) -> None:
        request = self._request()
        artifact = MeasurementArtifact(
            request.request_id, request.producer_id, request.producer_version,
            'monetization_path', '0.1', request.evidence_ids,
            self.producer.measurement_method,
            {
                'source_reference': self.evidence.raw_reference,
                'path': 'ADS',
                'evidence_kind': 'PLATFORM_AD_PROGRAM',
                'validation_rule': 'recognized_monetization_path_v1',
                'calculated_path': 'ADS',
            },
            'ADS',
            {'path_scope': 'ADS'},
        )
        with self.assertRaisesRegex(ValueError, 'provenance is missing: source'):
            self.production.produce(request, artifact)

    def test_monetization_producer_has_no_quality_agent_or_runtime_dependency(self) -> None:
        import ast
        for path in ('opportunity/facts/monetization.py', 'opportunity/facts/monetization_producer.py'):
            tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
            imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ('opportunity.fact_quality', 'AcceptedFact', 'crawlers', 'adapters', 'agents', 'runtime', 'governance', 'opportunity.judge'):
                self.assertNotIn(forbidden, imports)