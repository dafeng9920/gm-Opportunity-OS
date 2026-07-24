import ast
import unittest
from pathlib import Path

from candidates import CandidateRepository
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.analysis import AnalysisExecutionAuditStore, AnalysisExecutionStatus, AnalysisProposalReferenceValidator, AnalysisProposalStore, AnalysisRuntimeIdentity, AnalysisRuntimeRequest, DeterministicAnalysisRuntime
from opportunity.facts import FactProductionStore, MeasurementArtifact


class DeterministicAnalysisRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.25-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject("roblox.com", "roblox_game_page", "https://www.roblox.com/games/126884695634066/Grow-a-Garden")
        self.ledger.append(self.evidence)
        self.candidates = CandidateRepository(self.database)
        self.candidate = CandidatePacket("Grow a Garden", "recorded Roblox observation", (self.evidence.id,), "phase-18.18.1", 0.5)
        self.candidates.create(self.candidate)
        self.measurement = MeasurementArtifact("measurement-request", "fixture-producer", "0.1", "trend_up", "0.1", (self.evidence.id,), "fixture-measurement-v1", {"series_points": 1}, False, {"source": "recorded Roblox observation"})
        self.measurements = FactProductionStore(self.database)
        self.measurements.append_measurement(self.measurement)
        self.proposals = AnalysisProposalStore(self.database)
        self.audits = AnalysisExecutionAuditStore(self.database)
        self.identity = AnalysisRuntimeIdentity("deterministic-analysis-runtime", "0.1", "deterministic", "phase-18.25-config-v1")
        self.runtime = DeterministicAnalysisRuntime(self.identity, self.candidates, AnalysisProposalReferenceValidator(self.measurements, self.ledger), self.proposals, self.audits)

    def request(self, **changes) -> AnalysisRuntimeRequest:
        values = dict(candidate_id=self.candidate.id, measurement_artifact_ids=(self.measurement.artifact_id,), evidence_ids=(self.evidence.id,), requested_fact_id="trend_up", requested_fact_version="0.1", context={"purpose": "runtime-container-test"})
        values.update(changes)
        return AnalysisRuntimeRequest(**values)

    def test_valid_execution_creates_non_authoritative_proposal_and_execution_identity(self) -> None:
        result = self.runtime.execute(self.request())

        self.assertEqual(result.audit.status, AnalysisExecutionStatus.SUCCEEDED)
        self.assertFalse(result.replayed)
        self.assertIsNotNone(result.proposal)
        assert result.proposal is not None
        self.assertEqual(result.proposal.status.value, "NON_AUTHORITATIVE")
        self.assertEqual(result.proposal.runtime_identity, "deterministic-analysis-runtime@0.1")
        self.assertEqual(result.audit.runtime_id, self.identity.runtime_id)
        self.assertEqual(result.audit.runtime_version, self.identity.runtime_version)
        self.assertEqual(result.audit.executor_type, "deterministic")
        self.assertEqual(result.audit.configuration_reference, "phase-18.25-config-v1")
        self.assertTrue(result.audit.executed_at)

    def test_runtime_reads_only_scoped_references_and_preserves_provenance_trace(self) -> None:
        result = self.runtime.execute(self.request())
        assert result.proposal is not None

        self.assertEqual(self.candidates.get(result.proposal.candidate_id).id, self.candidate.id)  # type: ignore[union-attr]
        self.assertEqual(result.proposal.measurement_artifact_ids, (self.measurement.artifact_id,))
        self.assertEqual(result.proposal.evidence_ids, (self.evidence.id,))
        self.assertIsNotNone(self.measurements.get_measurement(self.measurement.artifact_id))
        self.assertEqual(self.ledger.get(self.evidence.id).id, self.evidence.id)  # type: ignore[union-attr]
        self.assertEqual(result.audit.proposal_id, result.proposal.proposal_id)
        self.assertEqual(self.proposals.get(result.proposal.proposal_id), result.proposal)

    def test_runtime_has_no_fact_gate_judge_or_triad_write_path(self) -> None:
        for method in ("produce", "create_fact", "accept_fact", "evaluate_gate", "write_judge", "write_triad", "write_decision"):
            self.assertFalse(hasattr(self.runtime, method))
        tree = ast.parse(Path("opportunity/analysis/runtime.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("opportunity.facts", "opportunity.fact_quality", "opportunity.gate_evaluation", "opportunity.judge", "opportunity.triad_evaluation", "opportunity.assessments"):
            self.assertNotIn(forbidden, imports)

    def test_invalid_references_and_unsupported_fact_create_audit_only(self) -> None:
        invalid_requests = (
            self.request(measurement_artifact_ids=("unknown-measurement",)),
            self.request(evidence_ids=("unknown-evidence",)),
            self.request(requested_fact_id="new-analysis-fact"),
        )
        for request in invalid_requests:
            result = self.runtime.execute(request)
            self.assertEqual(result.audit.status, AnalysisExecutionStatus.REJECTED_PRE_EXECUTION)
            self.assertIsNone(result.proposal)
            self.assertIsNone(result.audit.proposal_id)
            self.assertIsNotNone(result.audit.failure_category)
        with self.assertRaises(TypeError):
            AnalysisRuntimeRequest(self.candidate.id, (self.measurement.artifact_id,), (self.evidence.id,), "trend_up", "0.1", accepted_fact_id="not-an-input")  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            AnalysisRuntimeRequest(self.candidate.id, (self.measurement.artifact_id,), (self.evidence.id,), "trend_up", "0.1", gate_reference="not-an-input")  # type: ignore[call-arg]

    def test_intentional_repeat_creates_new_event_and_transport_retry_replays(self) -> None:
        first = self.runtime.execute(self.request())
        second = self.runtime.execute(self.request())
        self.assertNotEqual(first.proposal.proposal_id, second.proposal.proposal_id)  # type: ignore[union-attr]
        retry_request = self.request(idempotency_key="transport-retry-1")
        original = self.runtime.execute(retry_request)
        replay = self.runtime.execute(retry_request)
        self.assertEqual(original.proposal.proposal_id, replay.proposal.proposal_id)  # type: ignore[union-attr]
        self.assertEqual(original.audit.invocation_id, replay.audit.invocation_id)
        self.assertTrue(replay.replayed)
        with self.assertRaisesRegex(ValueError, "different analysis request"):
            self.runtime.execute(self.request(context={"purpose": "different"}, idempotency_key="transport-retry-1"))

    def test_deterministic_output_has_no_fact_value_or_recommendation(self) -> None:
        result = self.runtime.execute(self.request())
        assert result.proposal is not None
        self.assertEqual(result.proposal.analysis_summary, "insufficient deterministic measurements for transformation")
        self.assertIn("authorized review and a fact-specific producer are required", result.proposal.missing_information)
        self.assertNotIn("recommendation", result.proposal.__dataclass_fields__)
        self.assertNotIn("opportunity_score", result.proposal.__dataclass_fields__)


if __name__ == "__main__":
    unittest.main()
