"""Phase 18.22: a deterministic simulation of the non-authoritative proposal path."""
from __future__ import annotations

import unittest
from dataclasses import dataclass
from pathlib import Path

from adapters.roblox import RecordedRobloxGameAdapter
from candidates import EvidenceReferenceValidator
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, CandidatePacket, Component
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from opportunity.analysis import AnalysisProposal, AnalysisProposalReferenceValidator, AnalysisProposalStatus, AnalysisProposalStore
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore, QualityStatus
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, SourceInventoryProducer
from opportunity.gate_evaluation import MultiFactGateEvaluator
from tests.test_phase_18_18_1_roblox_input_layer import GAME_URL, observations


class InMemoryMeasurements:
    """Test-only existing-artifact lookup before the production boundary persists it."""

    def __init__(self, *artifacts) -> None:
        self._artifacts = {artifact.artifact_id: artifact for artifact in artifacts}

    def get_measurement(self, artifact_id: str):
        return self._artifacts.get(artifact_id)


@dataclass(frozen=True, slots=True)
class AuthorizedReview:
    """Ephemeral, deterministic confirmation; it has no Fact-producing authority."""

    proposal_id: str
    producer_id: str
    producer_version: str
    measurement_artifact_id: str
    transformation_method: str


class DeterministicProposalReview:
    """Test-only simulation of an authorized reviewer before the frozen production boundary."""

    def __init__(self, references, measurements, producers) -> None:
        self._references = references
        self._measurements = measurements
        self._producers = producers

    def approve(self, proposal: AnalysisProposal, producer_id: str, producer_version: str, transformation_method: str) -> AuthorizedReview:
        self._references.validate(proposal)
        if len(proposal.measurement_artifact_ids) != 1:
            raise ValueError("simulation requires exactly one measurement artifact")
        artifact = self._measurements.get_measurement(proposal.measurement_artifact_ids[0])
        producer = self._producers.get(producer_id, producer_version)
        if producer is None:
            raise KeyError("reviewed fact producer is not registered")
        support = next((item for item in producer.supported_facts if (item.fact_id, item.fact_version) == (proposal.requested_fact_id, proposal.requested_fact_version)), None)
        if support is None:
            raise ValueError("reviewed producer is not authorized for requested fact")
        if transformation_method != artifact.measurement_method or transformation_method not in support.measurement_methods:
            raise ValueError("declared transformation method is not authorized")
        if tuple(artifact.evidence_ids) != proposal.evidence_ids:
            raise ValueError("proposal evidence lineage does not match measurement artifact")
        return AuthorizedReview(proposal.proposal_id, producer_id, producer_version, artifact.artifact_id, transformation_method)


class AnalysisProposalRuntimeSimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.22-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        registry = ComponentRegistry(self.database)
        registry.register(Component("adapter.roblox-recorded-game", "Recorded Roblox Game Adapter", "adapter", "0.1", "active", "test adapter"))
        registry.register_adapter(AdapterRegistration("adapter.roblox-recorded-game", "manual-public-capture", "0.1", "manual-public-capture-v0", "crawler.v0", "active"))
        self.ledger = EvidenceLedger(self.database)
        self.evidence = CrawlerContractRunner(registry, self.ledger).collect(RecordedRobloxGameAdapter(observations()), CrawlRequest("roblox", GAME_URL))
        self.candidate = CandidatePacket("[Roblox] Grow a Garden", "test candidate", tuple(item.id for item in self.evidence), "evidence-ledger", 0.5)
        self.producer = SourceInventoryProducer(self.ledger, {"roblox_game_page": "official", "roblox_game_stats": "community"})
        self.producers = FactProducerRegistry()
        self.producers.register(self.producer.registration())
        self.request = FactProductionRequest(self.producer.producer_id, self.producer.producer_version, "available_sources", "0.1", self.candidate.evidence_ids)
        self.measurement = self.producer.measure(self.request)
        self.measurements = InMemoryMeasurements(self.measurement)
        self.references = AnalysisProposalReferenceValidator(self.measurements, self.ledger)
        self.review = DeterministicProposalReview(self.references, self.measurements, self.producers)
        self.proposal_store = AnalysisProposalStore(self.database)
        self.production_store = FactProductionStore(self.database)
        self.production = FactProductionBoundary(self.producers, EvidenceReferenceValidator(self.ledger), self.production_store)
        policies = FactQualityRegistry()
        policies.register(FactQualityPolicy("available-sources-quality", "available_sources", "0.1", ("source_inventory", "method", "captured_at"), ("source_records",), 2, ("explicit-classification",), "0.1"))
        self.quality = FactQualityBoundary(policies, FactQualityStore(self.database))

    def proposal(self, **changes) -> AnalysisProposal:
        values = dict(candidate_id=self.candidate.id, measurement_artifact_ids=(self.measurement.artifact_id,), evidence_ids=self.candidate.evidence_ids, requested_fact_id="available_sources", requested_fact_version="0.1", analysis_summary="Request review of the already measured public-source inventory.", assumptions=("source classifications are explicitly declared",), uncertainty=("the proposal makes no opportunity conclusion",), missing_information=("none for the source-inventory measurement",))
        values.update(changes)
        return AnalysisProposal(**values)

    def test_approved_proposal_can_use_existing_authorized_production_and_quality_path(self) -> None:
        proposal = self.proposal()
        self.proposal_store.append(proposal)
        review = self.review.approve(proposal, self.producer.producer_id, self.producer.producer_version, self.producer.measurement_method)
        produced = self.production.produce(self.request, self.measurement)
        assessment, accepted = self.quality.assess(produced, self.measurement)

        self.assertEqual(proposal.status, AnalysisProposalStatus.NON_AUTHORITATIVE)
        self.assertEqual(review.proposal_id, proposal.proposal_id)
        self.assertEqual(review.measurement_artifact_id, produced.measurement_artifact_id)
        self.assertEqual(produced.fact.evidence_ids, self.candidate.evidence_ids)
        self.assertEqual(produced.fact.provenance["method"], review.transformation_method)
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)

    def test_proposal_is_not_a_fact_accepted_fact_or_gate_input(self) -> None:
        proposal = self.proposal()
        for method in ("to_evaluation_fact", "to_accepted_fact", "to_gate_input", "to_judge_input", "to_decision_artifact"):
            self.assertFalse(hasattr(proposal, method))
        with self.assertRaisesRegex(TypeError, "AcceptedFact lookup"):
            MultiFactGateEvaluator(proposal)  # type: ignore[arg-type]

    def test_review_rejects_unknown_producer_unsupported_fact_and_method(self) -> None:
        proposal = self.proposal()
        with self.assertRaisesRegex(KeyError, "not registered"):
            self.review.approve(proposal, "unknown-producer", "0.1", self.producer.measurement_method)
        unsupported = self.proposal(requested_fact_id="trend_up")
        with self.assertRaisesRegex(ValueError, "not authorized for requested fact"):
            self.review.approve(unsupported, self.producer.producer_id, self.producer.producer_version, self.producer.measurement_method)
        with self.assertRaisesRegex(ValueError, "transformation method"):
            self.review.approve(proposal, self.producer.producer_id, self.producer.producer_version, "undeclared-method")

    def test_reference_integrity_rejects_missing_measurement_and_evidence_lineage(self) -> None:
        with self.assertRaisesRegex(KeyError, "measurement artifact not found"):
            self.review.approve(self.proposal(measurement_artifact_ids=("fabricated-measurement",)), self.producer.producer_id, self.producer.producer_version, self.producer.measurement_method)
        with self.assertRaisesRegex(KeyError, "evidence not found"):
            self.review.approve(self.proposal(evidence_ids=("fabricated-evidence",)), self.producer.producer_id, self.producer.producer_version, self.producer.measurement_method)

    def test_schema_rejects_new_fact_version_and_decision_or_score_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown gate fact version"):
            self.proposal(requested_fact_id="proposal_new_fact")
        with self.assertRaisesRegex(ValueError, "unknown gate fact version"):
            self.proposal(requested_fact_version="0.2")
        with self.assertRaises(TypeError):
            self.proposal(recommendation="copy this game")
        with self.assertRaises(TypeError):
            self.proposal(hidden_score=99)

    def test_runtime_trace_is_review_proposal_measurement_evidence_but_not_persisted_on_fact(self) -> None:
        proposal = self.proposal()
        self.proposal_store.append(proposal)
        review = self.review.approve(proposal, self.producer.producer_id, self.producer.producer_version, self.producer.measurement_method)
        produced = self.production.produce(self.request, self.measurement)

        self.assertEqual(self.proposal_store.get(review.proposal_id), proposal)
        self.assertEqual(review.measurement_artifact_id, self.measurement.artifact_id)
        self.assertEqual(tuple(self.measurement.evidence_ids), proposal.evidence_ids)
        self.assertEqual(produced.measurement_artifact_id, review.measurement_artifact_id)
        self.assertNotIn("analysis_proposal_id", produced.fact.provenance)

