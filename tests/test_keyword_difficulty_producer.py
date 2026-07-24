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
    KeywordDifficultyProducer,
    MeasurementArtifact,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus


class KeywordDifficultyProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'keyword-difficulty-{self._testMethodName}.db'
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = self._serp_evidence((20, 25, 30))
        self.ledger.append(self.evidence)
        self.candidate = CandidatePacket(
            'Grow a Garden', 'recorded SERP signal', (self.evidence.id,), 'evidence-ledger', 0.5
        )
        self.producer = KeywordDifficultyProducer(self.ledger)
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
            'keyword-difficulty-quality', 'keyword_difficulty', '0.1',
            ('query', 'source', 'method', 'captured_at'),
            ('source_reference', 'query', 'ranked_results', 'calculation_rule', 'calculated_score'),
            1, ('reproducible-serp-calculation',), '0.1',
        )

    @staticmethod
    def _serp_evidence(scores, metadata=None) -> EvidenceObject:
        raw_reference = 'https://www.google.com/search?q=Grow+a+Garden+codes'
        data = {
            'keyword_difficulty_measurement': {
                'source_reference': raw_reference,
                'query': 'Grow a Garden codes',
                'ranked_results': tuple(
                    {
                        'position': index + 1,
                        'domain': f'result-{index + 1}.example',
                        'competition_score': score,
                    }
                    for index, score in enumerate(scores)
                ),
                'calculation_rule': 'mean_result_competition_score_v1',
            },
        }
        if metadata is not None:
            data = metadata
        return EvidenceObject('search-snapshot', 'serp-snapshot', raw_reference, metadata=data)

    def _request(self, evidence_id=None) -> FactProductionRequest:
        return FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'keyword_difficulty', '0.1', (evidence_id or self.evidence.id,),
        )

    def test_recorded_serp_evidence_produces_accepted_fact_and_competition_pass(self) -> None:
        request = self._request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        assessment, accepted = self.quality.assess(produced, artifact)

        self.assertEqual(artifact.output_value, 25.0)
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            self.candidate, 'competition', {'keyword_difficulty': accepted.fact.value}
        )
        self.assertEqual(gate.status, GateStatus.PASS)

    def test_high_recorded_competition_score_fails_competition_gate(self) -> None:
        evidence = self._serp_evidence((60, 70, 80))
        self.ledger.append(evidence)
        request = self._request(evidence.id)
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        _, accepted = self.quality.assess(produced, artifact)
        self.assertIsNotNone(accepted)
        gate = OpportunityGateEngine().evaluate(
            CandidatePacket('Competitive', 'recorded SERP signal', (evidence.id,), 'evidence-ledger', 0.5),
            'competition', {'keyword_difficulty': accepted.fact.value},
        )
        self.assertEqual(gate.status, GateStatus.FAIL)

    def test_absent_keyword_difficulty_leaves_competition_gate_unknown(self) -> None:
        gate = OpportunityGateEngine().evaluate(self.candidate, 'competition', {})
        self.assertEqual(gate.status, GateStatus.UNKNOWN)

    def test_missing_measurement_cannot_produce_keyword_difficulty_fact(self) -> None:
        evidence = self._serp_evidence((), {})
        self.ledger.append(evidence)
        with self.assertRaisesRegex(ValueError, 'missing measurement'):
            self.producer.measure(self._request(evidence.id))

    def test_missing_evidence_provenance_cannot_become_accepted_fact(self) -> None:
        request = self._request()
        artifact = MeasurementArtifact(
            request.request_id, request.producer_id, request.producer_version,
            'keyword_difficulty', '0.1', request.evidence_ids,
            self.producer.measurement_method,
            {
                'source_reference': self.evidence.raw_reference,
                'query': 'Grow a Garden codes',
                'ranked_results': ({'position': 1}, {'position': 2}, {'position': 3}),
                'calculation_rule': 'mean_result_competition_score_v1',
                'calculated_score': 25.0,
            },
            25.0,
            {'query': 'Grow a Garden codes'},
        )
        with self.assertRaisesRegex(ValueError, 'provenance is missing: source'):
            self.production.produce(request, artifact)

    def test_keyword_difficulty_producer_has_no_quality_agent_or_runtime_dependency(self) -> None:
        import ast
        for path in ('opportunity/facts/keyword_difficulty.py', 'opportunity/facts/keyword_difficulty_producer.py'):
            tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
            imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ('opportunity.fact_quality', 'AcceptedFact', 'crawlers', 'adapters', 'agents', 'runtime', 'governance', 'opportunity.judge'):
                self.assertNotIn(forbidden, imports)