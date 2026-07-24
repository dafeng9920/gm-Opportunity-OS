import ast
import sqlite3
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from core.schemas import EvidenceObject
from evidence import EvidenceLedger
from opportunity.analysis import AnalysisProposal, AnalysisProposalReferenceValidator, AnalysisProposalStatus, AnalysisProposalStore
from opportunity.fact_quality import AcceptedFact
from opportunity.facts import FactProductionStore, MeasurementArtifact
from opportunity.gate_evaluation import MultiFactGateEvaluator


class AnalysisProposalContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"analysis-proposal-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject("fixture", "raw", "https://example.test/evidence")
        self.ledger.append(self.evidence)
        self.measurement = MeasurementArtifact("request-1", "fixture-producer", "0.1", "trend_up", "0.1", (self.evidence.id,), "fixture-v1", {"series_points": 2}, True, {"source": "fixture"})
        self.measurements = FactProductionStore(self.database)
        self.measurements.append_measurement(self.measurement)
        self.validator = AnalysisProposalReferenceValidator(self.measurements, self.ledger)

    def proposal(self, **changes) -> AnalysisProposal:
        values = dict(candidate_id="candidate-1", measurement_artifact_ids=(self.measurement.artifact_id,), evidence_ids=(self.evidence.id,), requested_fact_id="trend_up", requested_fact_version="0.1", analysis_summary="A future reviewer should verify the supplied measurement.", assumptions=("two source points are present",), uncertainty=("source freshness is not independently verified",), missing_information=("source-observation timestamp",), model_identity=None, model_version=None, runtime_identity=None, prompt_reference_id=None)
        values.update(changes)
        return AnalysisProposal(**values)

    def test_valid_non_authoritative_proposal_is_immutable_and_append_only(self) -> None:
        proposal = self.proposal()
        self.validator.validate(proposal)
        self.assertEqual(proposal.status, AnalysisProposalStatus.NON_AUTHORITATIVE)
        with self.assertRaises(FrozenInstanceError):
            proposal.status = AnalysisProposalStatus.NON_AUTHORITATIVE  # type: ignore[misc]
        store = AnalysisProposalStore(self.database)
        store.append(proposal)
        self.assertEqual(store.get(proposal.proposal_id), proposal)
        with self.assertRaises(sqlite3.IntegrityError):
            store.append(proposal)
        self.assertFalse(hasattr(store, "update"))
        self.assertFalse(hasattr(store, "delete"))

    def test_reference_validator_requires_existing_measurement_and_evidence_in_measurement_scope(self) -> None:
        self.validator.validate(self.proposal())
        with self.assertRaisesRegex(KeyError, "measurement artifact not found"):
            self.validator.validate(self.proposal(measurement_artifact_ids=("missing-measurement",)))
        with self.assertRaisesRegex(KeyError, "evidence not found"):
            self.validator.validate(self.proposal(evidence_ids=("missing-evidence",)))
        outside = EvidenceObject("fixture", "raw", "https://example.test/outside")
        self.ledger.append(outside)
        with self.assertRaisesRegex(ValueError, "outside referenced measurement scope"):
            self.validator.validate(self.proposal(evidence_ids=(outside.id,)))

    def test_proposal_cannot_create_new_fact_id_or_authoritative_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown gate fact version"):
            self.proposal(requested_fact_id="analysis_new_fact")
        with self.assertRaisesRegex(ValueError, "NON_AUTHORITATIVE"):
            self.proposal(status="AUTHORITATIVE")  # type: ignore[arg-type]

    def test_proposal_has_no_fact_gate_judge_triad_or_decision_conversion_path(self) -> None:
        proposal = self.proposal()
        for forbidden_method in ("to_evaluation_fact", "to_accepted_fact", "to_gate_input", "to_judge_input", "to_triad_context", "to_decision_artifact"):
            self.assertFalse(hasattr(proposal, forbidden_method))
        self.assertNotIsInstance(proposal, AcceptedFact)
        with self.assertRaisesRegex(TypeError, "AcceptedFact lookup"):
            MultiFactGateEvaluator(proposal)  # type: ignore[arg-type]

    def test_analysis_contract_has_no_governance_or_runtime_dependencies(self) -> None:
        for path in ("opportunity/analysis/contracts.py", "opportunity/analysis/reference_validator.py", "opportunity/analysis/store.py"):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ("opportunity.fact_quality", "opportunity.gate_evaluation", "opportunity.judge", "opportunity.triad_evaluation", "governance", "runtime", "agents", "adapters", "crawlers"):
                self.assertNotIn(forbidden, imports)
