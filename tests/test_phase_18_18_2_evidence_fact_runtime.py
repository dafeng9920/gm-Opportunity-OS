import unittest
from pathlib import Path

from adapters.roblox import RecordedRobloxGameAdapter
from candidates import EvidenceReferenceValidator
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from opportunity.facts import (
    FactProducerRegistry,
    FactProductionBoundary,
    FactProductionRequest,
    FactProductionStore,
    RobloxObservationFactProducer,
)
from tests.test_phase_18_18_1_roblox_input_layer import GAME_URL, observations


class RobloxEvidenceFactRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.18.2-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        registry = ComponentRegistry(self.database)
        registry.register(Component("adapter.roblox-recorded-game", "Recorded Roblox Game Adapter", "adapter", "0.1", "active", "test adapter"))
        registry.register_adapter(AdapterRegistration("adapter.roblox-recorded-game", "manual-public-capture", "0.1", "manual-public-capture-v0", "crawler.v0", "active"))
        self.ledger = EvidenceLedger(self.database)
        self.evidence = CrawlerContractRunner(registry, self.ledger).collect(RecordedRobloxGameAdapter(observations()), CrawlRequest("roblox", GAME_URL))
        self.producer = RobloxObservationFactProducer(self.ledger)
        self.producers = FactProducerRegistry()
        self.producers.register(self.producer.registration())
        self.boundary = FactProductionBoundary(self.producers, EvidenceReferenceValidator(self.ledger), FactProductionStore(self.database))

    def request(self, fact_id: str = "game_title_observed") -> FactProductionRequest:
        return FactProductionRequest(self.producer.producer_id, self.producer.producer_version, fact_id, "0.1", (self.evidence[0].id,))

    def test_evidence_creates_a_valid_neutral_measurement_artifact(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        self.assertEqual(artifact.output_value, "[🏴‍☠️] Grow a Garden 🌶️")
        self.assertEqual(artifact.evidence_ids, (self.evidence[0].id,))
        self.assertEqual(artifact.producer_id, self.producer.producer_id)
        self.assertEqual(artifact.provenance["source_evidence_id"], self.evidence[0].id)
        self.assertEqual(artifact.provenance["producer_version"], "0.1")
        self.assertEqual(artifact.captured_at, self.evidence[0].captured_time)

    def test_provenance_traces_the_measurement_back_to_ledger_evidence(self) -> None:
        artifact = self.producer.measure(self.request("creator_observed"))
        source = self.ledger.get(artifact.provenance["source_evidence_id"])
        self.assertIsNotNone(source)
        assert source is not None
        self.assertEqual(source.metadata["source_locator"], GAME_URL)
        self.assertEqual(artifact.output_value, "The Garden Game")

    def test_frozen_gate_fact_contract_rejects_neutral_observation_fact_ids(self) -> None:
        request = self.request()
        artifact = self.producer.measure(request)
        with self.assertRaisesRegex(ValueError, "unknown gate fact version"):
            self.boundary.produce(request, artifact)

    def test_producer_rejects_judgement_named_requests(self) -> None:
        for forbidden in ("viral_game", "good_opportunity", "high_quality_game", "copy_this_game"):
            with self.assertRaisesRegex(ValueError, "producer capability"):
                self.producer.measure(self.request(forbidden))



