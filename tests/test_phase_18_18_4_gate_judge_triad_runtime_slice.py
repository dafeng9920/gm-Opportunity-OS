import unittest
from dataclasses import replace
from pathlib import Path

from adapters.roblox import RecordedRobloxGameAdapter
from candidates import CandidateRepository, EvidenceReferenceValidator
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, CandidatePacket, Component
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from governance.triad.contracts import Role
from governance.triad.execution import AuditReferenceValidator, DeterministicRoleRunner, RoleArtifactAssembler, RoleArtifactRuntime, RoleExecutionAuditStore, RoleInvocation, TriadExecutionContext
from opportunity.assessments import AssessmentRecordSource, AssessmentRecordWriter, JudgeAssessmentStore, JudgeRuntimeSource
from opportunity.fact_quality import FactQualityBoundary, FactQualityPolicy, FactQualityRegistry, FactQualityStore, QualityStatus
from opportunity.facts import FactProducerRegistry, FactProductionBoundary, FactProductionRequest, FactProductionStore, SourceInventoryProducer
from opportunity.gate_evaluation import GateAssessmentAssetStore, GateAssessmentAssetWriter, MultiFactGateEvaluator
from opportunity.judge import GateAssessmentJudgeInputAssembler, JudgeRuntimeAdapter, StaticJudgeAssessmentRuntime
from opportunity.triad_evaluation import RoleAssessmentRecord, TriadEvaluationAssembler, TriadRoleContract
from opportunity.triad_evaluation.decision_store import TriadDecisionStore
from opportunity.triad_evaluation.decision_writer import TriadDecisionArtifactWriter
from opportunity.triad_evaluation.store import RoleAssessmentStore
from opportunity.triad_identity import InvocationIdentityBinding, TriadIdentityLifecycle, TriadWorker, WorkerState
from tests.test_phase_18_18_1_roblox_input_layer import GAME_URL, observations


class GateJudgeTriadRuntimeSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"phase-18.18.4-{self._testMethodName}.db"
        self.database.unlink(missing_ok=True)
        registry = ComponentRegistry(self.database)
        registry.register(Component("adapter.roblox-recorded-game", "Recorded Roblox Game Adapter", "adapter", "0.1", "active", "test adapter"))
        registry.register_adapter(AdapterRegistration("adapter.roblox-recorded-game", "manual-public-capture", "0.1", "manual-public-capture-v0", "crawler.v0", "active"))
        self.ledger = EvidenceLedger(self.database)
        self.evidence = CrawlerContractRunner(registry, self.ledger).collect(RecordedRobloxGameAdapter(observations()), CrawlRequest("roblox", GAME_URL))
        self.candidate = CandidatePacket("[🏴‍☠️] Grow a Garden 🌶️", "evidence-backed candidate", tuple(item.id for item in self.evidence), "evidence-ledger", 0.5)
        self.candidates = CandidateRepository(self.database)
        self.candidates.create(self.candidate)
        self.producer = SourceInventoryProducer(self.ledger, {"roblox_game_page": "official", "roblox_game_stats": "community"})
        producers = FactProducerRegistry()
        producers.register(self.producer.registration())
        self.production_store = FactProductionStore(self.database)
        self.production = FactProductionBoundary(producers, EvidenceReferenceValidator(self.ledger), self.production_store)
        policies = FactQualityRegistry()
        policies.register(FactQualityPolicy("available-sources-quality", "available_sources", "0.1", ("source_inventory", "method", "captured_at"), ("source_records",), 2, ("explicit-classification",), "0.1"))
        self.quality_store = FactQualityStore(self.database)
        self.quality = FactQualityBoundary(policies, self.quality_store)
        self.asset_store = GateAssessmentAssetStore(self.database)

    def accepted_fact(self):
        request = FactProductionRequest(self.producer.producer_id, self.producer.producer_version, "available_sources", "0.1", self.candidate.evidence_ids)
        measurement = self.producer.measure(request)
        produced = self.production.produce(request, measurement)
        assessment, accepted = self.quality.assess(produced, measurement)
        self.assertEqual(assessment.status, QualityStatus.PASS)
        self.assertIsNotNone(accepted)
        return measurement, produced, accepted

    def gate_asset(self):
        measurement, produced, accepted = self.accepted_fact()
        gate = MultiFactGateEvaluator(self.quality_store).evaluate(self.candidate)
        asset = GateAssessmentAssetWriter(self.asset_store, self.candidates, self.quality_store).append(gate)
        return measurement, produced, accepted, gate, asset

    def judge_record(self, asset):
        assembler = GateAssessmentJudgeInputAssembler(self.candidates, EvidenceReferenceValidator(self.ledger), self.quality_store, self.asset_store)
        store = JudgeAssessmentStore(self.database)
        record = JudgeRuntimeAdapter(assembler, AssessmentRecordWriter(store), StaticJudgeAssessmentRuntime()).assess(asset)
        return assembler, store, record

    def triad_decision(self, asset, judge):
        audit = RoleExecutionAuditStore(self.database)
        runtime = RoleArtifactRuntime(DeterministicRoleRunner(audit), RoleArtifactAssembler(AuditReferenceValidator(audit)))
        execution = TriadExecutionContext("roblox-slice", "roblox-slice-task", self.candidate.id, judge.assessment_id, "0.1")
        role_artifacts = []
        previous_refs = (judge.assessment_id,)
        lifecycles = []
        for role in (Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE):
            worker = TriadWorker(f"worker-{role.value}", ("execute",), "0.1")
            lifecycle = TriadIdentityLifecycle(worker)
            lifecycle.assign(InvocationIdentityBinding(f"roblox-slice:{role.value}", worker.worker_id, role.value, "triad.static", (), (asset.asset_id, judge.assessment_id), "RoleAssessmentRecord", "0.1"))
            lifecycle.execute()
            artifact = runtime.execute(execution, RoleInvocation(execution.execution_id, execution.governance_task_id, self.candidate.id, judge.assessment_id, role, previous_refs, "0.1"))
            release = lifecycle.release()
            self.assertIsNotNone(release)
            lifecycles.append(lifecycle)
            role_artifacts.append((role, artifact, release))
            previous_refs = artifact.input_refs
        roles = tuple(TriadRoleContract(role.value, role.value, ("GateAssessmentAsset",), ("GateAssessmentAsset",), ("Evidence", "MeasurementArtifact"), "RoleAssessmentRecord", "0.1") for role in (Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE))
        role_store = RoleAssessmentStore(self.database)
        role_records = tuple(RoleAssessmentRecord(f"role-{role.value}-{judge.assessment_id}", role.value, self.candidate.id, asset.asset_id, judge.assessment_id, JudgeRuntimeSource.STATIC_ONLY, judge.assessment.recommendation.value, (artifact.audit_refs[0], release.release_id), "0.1") for role, artifact, release in role_artifacts)
        for record in role_records:
            role_store.append(record)
        context = TriadEvaluationAssembler().assemble(self.candidate.id, asset.asset_id, roles, role_records)
        artifact = TriadDecisionArtifactWriter(role_store, TriadDecisionStore(self.database)).write(context)
        return artifact, role_records, role_artifacts, lifecycles, audit

    def test_real_roblox_chain_reaches_persisted_static_judge_and_triad_decision_artifact(self) -> None:
        measurement, produced, accepted, gate, asset = self.gate_asset()
        assembler, judge_store, judge = self.judge_record(asset)
        decision, role_records, role_artifacts, lifecycles, audit = self.triad_decision(asset, judge)

        self.assertEqual(asset.candidate_id, self.candidate.id)
        self.assertIn(accepted.accepted_fact_id, asset.fact_refs)
        self.assertEqual(judge.source, AssessmentRecordSource.STATIC_TEST_ONLY)
        self.assertEqual(judge.runtime_id, "STATIC_ONLY")
        self.assertEqual(judge.input_asset_id, asset.asset_id)
        self.assertEqual(decision.candidate_id, self.candidate.id)
        self.assertEqual(decision.input_asset_id, asset.asset_id)
        self.assertEqual(len(role_records), 3)
        self.assertEqual(len(audit.list()), 3)
        self.assertTrue(all(item.state is WorkerState.WHITE_STATE and item.binding is None and len(item.releases) == 1 for item in lifecycles))
        self.assertEqual(judge_store.get(judge.assessment_id), judge)

    def test_decision_artifact_traces_to_real_evidence_measurement_fact_quality_asset_judge_and_audit(self) -> None:
        measurement, produced, accepted, _, asset = self.gate_asset()
        _, _, judge = self.judge_record(asset)
        decision, role_records, _, _, audit = self.triad_decision(asset, judge)

        self.assertEqual(measurement.evidence_ids, self.candidate.evidence_ids)
        self.assertEqual(produced.measurement_artifact_id, measurement.artifact_id)
        self.assertEqual(accepted.source_fact_id, produced.production_id)
        self.assertEqual(asset.fact_refs, (accepted.accepted_fact_id,))
        self.assertEqual({record.input_asset_id for record in role_records}, {asset.asset_id})
        self.assertEqual({record.judge_assessment_id for record in role_records}, {judge.assessment_id})
        self.assertEqual(set(decision.role_assessment_refs), {record.role_assessment_id for record in role_records})
        self.assertTrue(all(audit.get(record.provenance[0]) is not None for record in role_records))
        self.assertTrue(all(self.ledger.get(evidence_id) is not None for evidence_id in measurement.evidence_ids))

    def test_judge_requires_persisted_gate_asset_but_current_judge_input_contains_evidence(self) -> None:
        _, _, _, _, asset = self.gate_asset()
        assembler, _, _ = self.judge_record(asset)
        unpersisted = replace(asset, asset_id="unpersisted-gate-asset")
        with self.assertRaisesRegex(ValueError, "persisted"):
            assembler.assemble(unpersisted)
        judge_input = assembler.assemble(asset)
        self.assertEqual(tuple(item.id for item in judge_input.evidence), self.candidate.evidence_ids)

    def test_asset_writer_rejects_gate_record_claiming_missing_accepted_fact(self) -> None:
        _, _, _, gate, _ = self.gate_asset()
        forged = replace(gate, fact_refs=("missing-accepted-fact",))
        with self.assertRaisesRegex(ValueError, "outside accepted fact scope"):
            GateAssessmentAssetWriter(self.asset_store, self.candidates, self.quality_store).append(forged)

    def test_assembler_rejects_wrong_candidate_asset(self) -> None:
        _, _, _, _, asset = self.gate_asset()
        tampered = replace(asset, asset_id="wrong-candidate-asset", candidate_id="other-candidate")
        self.asset_store.append(tampered)
        assembler = GateAssessmentJudgeInputAssembler(self.candidates, EvidenceReferenceValidator(self.ledger), self.quality_store, self.asset_store)
        with self.assertRaisesRegex(KeyError, "candidate not found"):
            assembler.assemble(tampered)

    def test_failed_quality_fact_is_not_available_to_gate_evaluator(self) -> None:
        request = FactProductionRequest(self.producer.producer_id, self.producer.producer_version, "available_sources", "0.1", self.candidate.evidence_ids)
        measurement = self.producer.measure(request)
        produced = self.production.produce(request, measurement)
        policies = FactQualityRegistry()
        policies.register(FactQualityPolicy("available-sources-failing-quality", "available_sources", "0.1", ("source_inventory", "method", "captured_at"), ("source_records", "required_but_absent"), 2, ("explicit-classification",), "0.1"))
        failing_store = FactQualityStore(self.database)
        assessment, accepted = FactQualityBoundary(policies, failing_store).assess(produced, measurement)
        self.assertEqual(assessment.status, QualityStatus.FAIL)
        self.assertIsNone(accepted)
        gate = MultiFactGateEvaluator(failing_store).evaluate(self.candidate)
        self.assertIn("missing_fact:available_sources", gate.reason_codes)
    def test_unreleased_identity_is_not_currently_rejected_by_triad_decision_writer(self) -> None:
        _, _, _, _, asset = self.gate_asset()
        _, _, judge = self.judge_record(asset)
        worker = TriadWorker("unreleased-worker", ("execute",), "0.1")
        lifecycle = TriadIdentityLifecycle(worker)
        lifecycle.assign(InvocationIdentityBinding("unreleased", worker.worker_id, "execution", "triad.static", (), (asset.asset_id,), "RoleAssessmentRecord", "0.1"))
        lifecycle.execute()
        self.assertEqual(lifecycle.state, WorkerState.EXECUTING)
        self.assertEqual(lifecycle.releases, [])



