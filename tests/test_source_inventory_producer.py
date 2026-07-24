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
    SourceInventoryProducer,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus


class SourceInventoryProducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path('.opportunity-os') / f'source-inventory-{self._testMethodName}.db'
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.official = EvidenceObject(
            'roblox.com', 'official-game-entity',
            'https://www.roblox.com/games/126884695634066/Grow-a-Garden',
            metadata={'game_name': 'Grow a Garden', 'claim_scope': 'official entity'},
        )
        self.community = EvidenceObject(
            'growagarden.wiki', 'community-update-log',
            'https://growagarden.wiki/Update_Log/1.07.0',
            metadata={'game_name': 'Grow a Garden', 'claim_scope': 'community update log'},
        )
        self.ledger.append(self.official)
        self.ledger.append(self.community)
        self.producer = SourceInventoryProducer(self.ledger)
        producers = FactProducerRegistry()
        producers.register(self.producer.registration())
        self.production = FactProductionBoundary(
            producers, EvidenceReferenceValidator(self.ledger), FactProductionStore(self.database)
        )
        self.quality_store = FactQualityStore(self.database)
        policies = FactQualityRegistry()
        policies.register(FactQualityPolicy(
            'available-sources-quality', 'available_sources', '0.1',
            ('source_inventory', 'method', 'captured_at'),
            ('source_records',), 2, ('explicit-classification',), '0.1',
        ))
        self.quality = FactQualityBoundary(policies, self.quality_store)
        self.candidate = CandidatePacket(
            'Grow a Garden', 'evidence-backed candidate',
            (self.official.id, self.community.id), 'evidence-ledger', 0.5,
        )

    def _request(self, evidence_ids=None) -> FactProductionRequest:
        return FactProductionRequest(
            self.producer.producer_id, self.producer.producer_version,
            'available_sources', '0.1',
            evidence_ids or self.candidate.evidence_ids,
        )

    def test_grow_a_garden_evidence_produces_accepted_data_gate_fact(self) -> None:
        request = self._request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        assessment, accepted = self.quality.assess(produced, artifact)

        self.assertEqual(artifact.output_value, ('official', 'community'))
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        self.assertEqual(accepted.fact.evidence_ids, self.candidate.evidence_ids)
        gate = OpportunityGateEngine().evaluate(
            self.candidate, 'data_availability', {'available_sources': accepted.fact.value}
        )
        self.assertEqual(gate.status, GateStatus.PASS)

    def test_unclassified_evidence_is_rejected_before_measurement_artifact(self) -> None:
        unknown = EvidenceObject('unknown.example', 'unclassified-source', 'https://unknown.example')
        self.ledger.append(unknown)
        with self.assertRaisesRegex(ValueError, 'no classification'):
            self.producer.measure(self._request((self.official.id, unknown.id)))

    def test_source_inventory_producer_has_no_collector_agent_or_runtime_dependency(self) -> None:
        import ast
        tree = ast.parse(Path('opportunity/facts/source_inventory.py').read_text(encoding='utf-8-sig'))
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ('crawlers', 'adapters', 'intelligence', 'agents', 'runtime', 'governance', 'opportunity.judge'):
            self.assertNotIn(forbidden, imports)