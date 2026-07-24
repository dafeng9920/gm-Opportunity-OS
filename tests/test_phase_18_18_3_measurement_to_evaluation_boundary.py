import unittest
from pathlib import Path

from adapters.roblox import RecordedRobloxGameAdapter
from candidates import EvidenceReferenceValidator
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, CandidatePacket, Component
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore, QualityStatus
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, MeasurementArtifact, SourceInventoryProducer
from opportunity.gate_evaluation import MultiFactGateEvaluator
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from tests.test_phase_18_18_1_roblox_input_layer import GAME_URL, observations


class MeasurementToEvaluationBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.18.3-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        registry = ComponentRegistry(self.database)
        registry.register(Component("adapter.roblox-recorded-game", "Recorded Roblox Game Adapter", "adapter", "0.1", "active", "test adapter"))
        registry.register_adapter(AdapterRegistration("adapter.roblox-recorded-game", "manual-public-capture", "0.1", "manual-public-capture-v0", "crawler.v0", "active"))
        self.ledger = EvidenceLedger(self.database)
        self.evidence = CrawlerContractRunner(registry, self.ledger).collect(RecordedRobloxGameAdapter(observations()), CrawlRequest("roblox", GAME_URL))
        self.candidate = CandidatePacket("[🏴‍☠️] Grow a Garden 🌶️", "evidence-backed candidate", tuple(item.id for item in self.evidence), "evidence-ledger", 0.5)
        self.producer = SourceInventoryProducer(self.ledger, {"roblox_game_page": "official", "roblox_game_stats": "community"})
        self.producers = FactProducerRegistry()
        self.producers.register(self.producer.registration())
        self.production_store = FactProductionStore(self.database)
        self.production = FactProductionBoundary(self.producers, EvidenceReferenceValidator(self.ledger), self.production_store)
        policies = FactQualityRegistry()
        policies.register(FactQualityPolicy("available-sources-quality", "available_sources", "0.1", ("source_inventory", "method", "captured_at"), ("source_records",), 2, ("explicit-classification",), "0.1"))
        self.quality_store = FactQualityStore(self.database)
        self.quality = FactQualityBoundary(policies, self.quality_store)

    def request(self, evidence_ids: tuple[str, ...] | None = None, fact_id: str = "available_sources", version: str = "0.1") -> FactProductionRequest:
        return FactProductionRequest(self.producer.producer_id, self.producer.producer_version, fact_id, version, evidence_ids or self.candidate.evidence_ids)

    def test_registered_authorized_path_transforms_measurement_to_evidence_backed_evaluation_fact(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        assessment, accepted = self.quality.assess(produced, artifact)

        self.assertEqual(artifact.output_value, ("official", "community"))
        self.assertEqual(produced.fact.fact_id, "available_sources")
        self.assertEqual(produced.fact.verification, FactVerification.EVIDENCE_BACKED)
        self.assertEqual(produced.fact.evidence_ids, self.candidate.evidence_ids)
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)

        gate_record = MultiFactGateEvaluator(self.quality_store).evaluate(self.candidate)
        self.assertIn(accepted.accepted_fact_id, gate_record.fact_refs)  # type: ignore[union-attr]
        self.assertNotIn("missing_fact:available_sources", gate_record.reason_codes)

    def test_provenance_chain_links_produced_fact_measurement_producer_and_evidence(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        stored_measurement = self.production_store.get_measurement(produced.measurement_artifact_id)

        self.assertIsNotNone(stored_measurement)
        self.assertEqual(produced.measurement_artifact_id, artifact.artifact_id)
        self.assertEqual(produced.producer_id, self.producer.producer_id)
        self.assertEqual(produced.producer_version, self.producer.producer_version)
        self.assertEqual(produced.fact.evidence_ids, self.candidate.evidence_ids)
        self.assertEqual(produced.fact.provenance["method"], self.producer.measurement_method)
        self.assertTrue(produced.fact.provenance["captured_at"])
        self.assertEqual(tuple(record["evidence_id"] for record in artifact.provenance["source_inventory"]), self.candidate.evidence_ids)

    def test_unregistered_producer_is_denied_at_transformation_boundary(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        denied = FactProductionBoundary(FactProducerRegistry(), EvidenceReferenceValidator(self.ledger), FactProductionStore(self.database))
        with self.assertRaisesRegex(KeyError, "not registered"):
            denied.produce(request, artifact)

    def test_unsupported_fact_id_and_version_are_denied_by_registered_producer(self) -> None:
        with self.assertRaisesRegex(ValueError, "producer capability"):
            self.producer.measure(self.request(fact_id="trend_up"))
        with self.assertRaisesRegex(ValueError, "producer capability"):
            self.producer.measure(self.request(version="0.2"))

    def test_quality_failure_keeps_valid_evaluation_fact_out_of_gate_input(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        produced = self.production.produce(request, artifact)
        failing_policies = FactQualityRegistry()
        failing_policies.register(FactQualityPolicy("available-sources-incomplete-quality", "available_sources", "0.1", ("source_inventory", "method", "captured_at"), ("source_records", "required_but_absent"), 2, ("explicit-classification",), "0.1"))
        failing_store = FactQualityStore(self.database)
        assessment, accepted = FactQualityBoundary(failing_policies, failing_store).assess(produced, artifact)

        self.assertEqual(assessment.status, QualityStatus.FAIL)
        self.assertIsNone(accepted)
        gate_record = MultiFactGateEvaluator(failing_store).evaluate(self.candidate)
        self.assertIn("missing_fact:available_sources", gate_record.reason_codes)
    def test_measurement_artifact_cannot_enter_gate_and_producer_has_no_direct_evaluation_fact_writer(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        self.assertIsInstance(artifact, MeasurementArtifact)
        self.assertFalse(hasattr(self.producer, "produce"))
        with self.assertRaisesRegex(TypeError, "AcceptedFact lookup"):
            MultiFactGateEvaluator(artifact)  # type: ignore[arg-type]

    def test_current_frozen_fact_contract_does_not_reject_extra_judgement_provenance(self) -> None:
        fact = EvaluationFact("available_sources", EvaluationFactCategory.DATA, ("official", "community"), self.candidate.evidence_ids, 1.0, FactVerification.EVIDENCE_BACKED, "0.1", {"source_inventory": "fixture", "method": "fixture", "captured_at": "2026-07-24T00:00:00+00:00", "recommendation": "copy_this_game", "opportunity_score": 99})
        self.assertEqual(fact.provenance["recommendation"], "copy_this_game")
        self.assertEqual(fact.provenance["opportunity_score"], 99)

