import unittest
from pathlib import Path

from adapters.roblox import RecordedRobloxGameAdapter, RecordedRobloxObservation
from candidates import CandidateFormationRequest, CandidateFormationService, CandidateRepository, EvidenceReferenceValidator
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, CandidatePacket, Component
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger

GAME_URL = "https://www.roblox.com/games/126884695634066/Grow-a-Garden"
CAPTURED_AT = "2026-07-24T00:00:00+00:00"


def observations() -> tuple[RecordedRobloxObservation, ...]:
    return (
        RecordedRobloxObservation("roblox-place-126884695634066-page-20260724", "roblox.com", "roblox_game_page", GAME_URL, CAPTURED_AT, "manual_public_page_capture", "title=[🏴‍☠️] Grow a Garden 🌶️; creator=The Garden Game; description=Welcome to Grow a Garden. Buy seeds, plant them, wait for them to grow, and collect the profits.", {"captured_by": "phase-18.18.1", "source_kind": "official_public_game_page"}, {"place_id": "126884695634066", "fields_observed": ("title", "creator", "description")}),
        RecordedRobloxObservation("roblox-place-126884695634066-stats-20260724", "robloxgames.org", "roblox_game_stats", "https://www.robloxgames.org/stats/grow-a-garden", CAPTURED_AT, "manual_public_stats_capture", "place_id=126884695634066; visits=35.0B+; active_players=112548; favorites=10744784", {"captured_by": "phase-18.18.1", "source_kind": "public_third_party_stats_page"}, {"place_id": "126884695634066", "fields_observed": ("visits", "active_players", "favorites")}),
    )


class RobloxInputLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.18.1-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        self.registry = ComponentRegistry(self.database)
        self.registry.register(Component("adapter.roblox-recorded-game", "Recorded Roblox Game Adapter", "adapter", "0.1", "active", "adapt supplied public Roblox observations into raw evidence"))
        self.registry.register_adapter(AdapterRegistration("adapter.roblox-recorded-game", "manual-public-capture", "0.1", "manual-public-capture-v0", "crawler.v0", "active"))
        self.ledger = EvidenceLedger(self.database)
        self.evidence = CrawlerContractRunner(self.registry, self.ledger).collect(RecordedRobloxGameAdapter(observations()), CrawlRequest("roblox", GAME_URL))

    def test_evidence_artifact_preserves_source_timestamp_and_provenance(self) -> None:
        stored = self.ledger.get(self.evidence[0].id)
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.source, "roblox.com")
        self.assertEqual(stored.captured_time, CAPTURED_AT)
        self.assertEqual(stored.metadata["source_locator"], GAME_URL)
        self.assertEqual(stored.metadata["acquisition_method"], "manual_public_page_capture")
        self.assertEqual(stored.metadata["raw_payload_reference"], stored.raw_reference)
        self.assertEqual(stored.metadata["provenance"]["source_kind"], "official_public_game_page")
        self.assertIn("Grow a Garden", stored.raw_reference)

    def test_candidate_creation_references_evidence_without_judgement(self) -> None:
        repository = CandidateRepository(self.database)
        result = CandidateFormationService(EvidenceReferenceValidator(self.ledger), repository, ("roblox",)).form(CandidateFormationRequest("roblox", "[🏴‍☠️] Grow a Garden 🌶️ (place 126884695634066)", tuple(item.id for item in self.evidence), "phase-18.18.1", "0.1", confidence=0.5))
        self.assertEqual(result.candidate_packet.evidence_ids, tuple(item.id for item in self.evidence))
        self.assertEqual(repository.get(result.candidate_id), result.candidate_packet)
        self.assertNotIn("opportunity_score", result.candidate_packet.to_dict())

    def test_candidate_contract_has_no_later_stage_judgement_fields(self) -> None:
        fields = set(CandidatePacket.__dataclass_fields__)
        for forbidden in ("opportunity_score", "recommendation", "success_probability", "quality_rating"):
            self.assertNotIn(forbidden, fields)



