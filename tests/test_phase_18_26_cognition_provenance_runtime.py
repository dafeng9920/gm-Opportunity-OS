import ast
import sqlite3
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from candidates import CandidateRepository, EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.analysis import AnalysisExecutionAuditStore, AnalysisProposal, AnalysisProposalReferenceValidator, AnalysisProposalStore, AnalysisRuntimeIdentity, AnalysisRuntimeRequest, CognitionLinkStatus, CognitionProvenanceLink, CognitionProvenanceLinkService, CognitionProvenanceLinkStore, DeterministicAnalysisRuntime
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, SourceInventoryProducer, TrendSignalProducer
from opportunity.gate_evaluation import MultiFactGateEvaluator


class MemoryMeasurements:
    def __init__(self, *artifacts) -> None:
        self._items = {artifact.artifact_id: artifact for artifact in artifacts}

    def get_measurement(self, artifact_id: str):
        return self._items.get(artifact_id)


class CognitionProvenanceRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.26-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        self.ledger = EvidenceLedger(self.database)
        self.page = EvidenceObject("roblox.com", "roblox_game_page", "https://www.roblox.com/games/126884695634066/Grow-a-Garden")
        self.stats = EvidenceObject("robloxgames.org", "roblox_game_stats", "https://www.robloxgames.org/stats/grow-a-garden")
        self.trend = EvidenceObject("trends.google.com", "trend-signal", "https://trends.google.com/trends/explore?geo=US&q=Grow%20a%20Garden", metadata={"query": "Grow a Garden", "region": "US", "trend_measurement": {"source_reference": "https://trends.google.com/trends/explore?geo=US&q=Grow%20a%20Garden", "time_window": ("2026-07-01", "2026-07-08"), "observations": (42, 67), "comparison_rule": "latest_gt_earliest"}})
        for item in (self.page, self.stats, self.trend):
            self.ledger.append(item)
        self.candidate = CandidatePacket("Grow a Garden", "recorded Roblox and trend observations", (self.page.id, self.stats.id, self.trend.id), "phase-18.18", 0.5)
        self.candidates = CandidateRepository(self.database)
        self.candidates.create(self.candidate)
        self.source = SourceInventoryProducer(self.ledger, {"roblox_game_page": "official", "roblox_game_stats": "community"})
        self.trend_producer = TrendSignalProducer(self.ledger)
        self.source_request = FactProductionRequest(self.source.producer_id, self.source.producer_version, "available_sources", "0.1", (self.page.id, self.stats.id))
        self.trend_request = FactProductionRequest(self.trend_producer.producer_id, self.trend_producer.producer_version, "trend_up", "0.1", (self.trend.id,))
        self.source_measurement = self.source.measure(self.source_request)
        self.trend_measurement = self.trend_producer.measure(self.trend_request)
        self.measurements = MemoryMeasurements(self.source_measurement, self.trend_measurement)
        self.proposals = AnalysisProposalStore(self.database)
        self.audits = AnalysisExecutionAuditStore(self.database)
        self.identity = AnalysisRuntimeIdentity("deterministic-analysis-runtime", "0.1", "deterministic", "phase-18.26-config-v1")
        self.runtime = DeterministicAnalysisRuntime(self.identity, self.candidates, AnalysisProposalReferenceValidator(self.measurements, self.ledger), self.proposals, self.audits)
        producers = FactProducerRegistry()
        producers.register(self.source.registration())
        producers.register(self.trend_producer.registration())
        self.production_store = FactProductionStore(self.database)
        self.production = FactProductionBoundary(producers, EvidenceReferenceValidator(self.ledger), self.production_store)
        self.source_produced = self.production.produce(self.source_request, self.source_measurement)
        self.trend_produced = self.production.produce(self.trend_request, self.trend_measurement)
        self.links = CognitionProvenanceLinkStore(self.database)
        self.link_service = CognitionProvenanceLinkService(self.proposals, AnalysisProposalReferenceValidator(self.production_store, self.ledger), self.production_store, self.links)

    def proposal(self):
        result = self.runtime.execute(AnalysisRuntimeRequest(self.candidate.id, (self.source_measurement.artifact_id, self.trend_measurement.artifact_id), self.candidate.evidence_ids, "trend_up", "0.1", {"purpose": "cognition-lineage-test"}))
        self.assertIsNotNone(result.proposal)
        return result.proposal

    def link(self, proposal, status=CognitionLinkStatus.PRODUCED, produced=None, **changes):
        values = dict(analysis_proposal_id=proposal.proposal_id, measurement_artifact_ids=proposal.measurement_artifact_ids, evidence_ids=proposal.evidence_ids, runtime_id=self.identity.runtime_id, runtime_version=self.identity.runtime_version, status=status)
        if produced is not None:
            values.update(produced_fact_id=produced.production_id, producer_event_id=produced.request_id)
        values.update(changes)
        return CognitionProvenanceLink(**values)

    def test_multiple_proposals_can_link_to_one_existing_produced_fact(self) -> None:
        first = self.proposal()
        second = self.proposal()
        first_link = self.link(first, produced=self.source_produced)
        second_link = self.link(second, produced=self.source_produced)
        self.link_service.record(first_link)
        self.link_service.record(second_link)

        self.assertEqual(self.links.get(first_link.cognition_link_id), first_link)
        self.assertEqual(self.links.get(second_link.cognition_link_id), second_link)
        self.assertEqual(first_link.produced_fact_id, second_link.produced_fact_id)
        self.assertEqual(self.production_store.get_produced(first_link.produced_fact_id).production_id, self.source_produced.production_id)  # type: ignore[union-attr]

    def test_one_proposal_can_have_separate_links_to_multiple_productions(self) -> None:
        proposal = self.proposal()
        source_link = self.link(proposal, produced=self.source_produced)
        trend_link = self.link(proposal, produced=self.trend_produced)
        self.link_service.record(source_link)
        self.link_service.record(trend_link)

        stored = self.links.list_for_proposal(proposal.proposal_id)
        self.assertEqual({link.produced_fact_id for link in stored}, {self.source_produced.production_id, self.trend_produced.production_id})
        self.assertNotEqual(self.source_produced.fact.fact_id, self.trend_produced.fact.fact_id)

    def test_rejected_proposal_lineage_is_retained_without_a_fact_link(self) -> None:
        proposal = self.proposal()
        link = self.link(proposal, status=CognitionLinkStatus.REJECTED, review_event_id="review-rejected-1")
        self.link_service.record(link)

        stored = self.links.get(link.cognition_link_id)
        self.assertEqual(stored.status, CognitionLinkStatus.REJECTED)  # type: ignore[union-attr]
        self.assertIsNone(stored.produced_fact_id)  # type: ignore[union-attr]

    def test_integrity_rejects_unknown_sources_and_unmatched_production(self) -> None:
        proposal = self.proposal()
        with self.assertRaisesRegex(KeyError, "analysis proposal not found"):
            self.link_service.record(self.link(proposal, analysis_proposal_id="unknown-proposal", produced=self.source_produced))
        missing_measurement = AnalysisProposal(self.candidate.id, ("unknown-measurement",), (self.page.id,), "trend_up", "0.1", "fixture", runtime_identity="deterministic-analysis-runtime@0.1")
        self.proposals.append(missing_measurement)
        with self.assertRaisesRegex(KeyError, "measurement artifact not found"):
            self.link_service.record(CognitionProvenanceLink(missing_measurement.proposal_id, ("unknown-measurement",), (self.page.id,), self.identity.runtime_id, self.identity.runtime_version, CognitionLinkStatus.PROPOSED))
        missing_evidence = AnalysisProposal(self.candidate.id, (self.source_measurement.artifact_id,), ("unknown-evidence",), "trend_up", "0.1", "fixture", runtime_identity="deterministic-analysis-runtime@0.1")
        self.proposals.append(missing_evidence)
        with self.assertRaisesRegex(KeyError, "evidence not found"):
            self.link_service.record(CognitionProvenanceLink(missing_evidence.proposal_id, (self.source_measurement.artifact_id,), ("unknown-evidence",), self.identity.runtime_id, self.identity.runtime_version, CognitionLinkStatus.PROPOSED))
        with self.assertRaisesRegex(KeyError, "produced fact not found"):
            self.link_service.record(self.link(proposal, produced_fact_id="fabricated-production", producer_event_id="fabricated-request"))
        with self.assertRaisesRegex(ValueError, "producer event"):
            self.link_service.record(self.link(proposal, produced=self.source_produced, producer_event_id="wrong-request"))

    def test_links_are_immutable_append_only_and_have_no_governance_authority(self) -> None:
        proposal = self.proposal()
        link = self.link(proposal, produced=self.source_produced)
        self.link_service.record(link)
        with self.assertRaises(FrozenInstanceError):
            link.status = CognitionLinkStatus.REJECTED  # type: ignore[misc]
        with self.assertRaises(sqlite3.IntegrityError):
            self.link_service.record(link)
        self.assertFalse(hasattr(self.links, "update"))
        self.assertFalse(hasattr(self.links, "delete"))
        for method in ("to_evaluation_fact", "to_accepted_fact", "to_gate_input", "to_judge_input", "to_triad_context", "to_decision_artifact", "produce"):
            self.assertFalse(hasattr(link, method))
        with self.assertRaisesRegex(TypeError, "AcceptedFact lookup"):
            MultiFactGateEvaluator(link)  # type: ignore[arg-type]

    def test_link_module_does_not_import_or_write_governance_boundaries(self) -> None:
        tree = ast.parse(Path("opportunity/analysis/cognition.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("opportunity.facts", "opportunity.fact_quality", "opportunity.gate_evaluation", "opportunity.judge", "opportunity.triad_evaluation", "opportunity.assessments"):
            self.assertNotIn(forbidden, imports)
        self.assertFalse(hasattr(self.link_service, "produce"))
        self.assertFalse(hasattr(self.link_service, "assess"))


if __name__ == "__main__":
    unittest.main()
