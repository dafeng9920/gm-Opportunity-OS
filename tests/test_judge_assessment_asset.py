import ast
import sqlite3
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from core.schemas import CandidatePacket, EvidenceObject
from opportunity.assessments import (
    AssessmentRecordSource,
    AssessmentRecordWriter,
    JudgeAssessmentRecord,
    JudgeAssessmentStore,
    JudgeInputHasher,
    JudgeRuntimeSource,
)
from opportunity.gates.contracts import GateStatus, OpportunityGateResult, RuleResult
from opportunity.judge import AssessmentRecommendation, JudgeAssessment, JudgeInput


class JudgeAssessmentAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"judge-assessment-asset-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.evidence = EvidenceObject("fixture", "signal", "https://example.test/evidence")
        self.candidate = CandidatePacket("Fixture", "signal", (self.evidence.id,), "fixture", 0.5)
        self.gate = OpportunityGateResult(
            self.candidate.id, "demand", "0.1", GateStatus.PASS, (self.evidence.id,),
            (RuleResult("trend_up", GateStatus.PASS, True, True),),
        )
        self.judge_input = JudgeInput(self.candidate, (self.evidence,), (self.gate,))
        self.assessment = JudgeAssessment(
            self.candidate.id, "Structured assessment fixture.", (),
            AssessmentRecommendation.SMALL_SCALE_VALIDATION, (self.evidence.id,), ("demand@0.1",),
        )
        self.store = JudgeAssessmentStore(self.database)
        self.writer = AssessmentRecordWriter(self.store)

    def record(self, source: AssessmentRecordSource = AssessmentRecordSource.STATIC_TEST_ONLY) -> JudgeAssessmentRecord:
        runtime_id = "STATIC_ONLY" if source is AssessmentRecordSource.STATIC_TEST_ONLY else "runtime.future-judge"
        runtime_version = "STATIC_ONLY" if source is AssessmentRecordSource.STATIC_TEST_ONLY else "1.0"
        audit_refs = () if source is AssessmentRecordSource.STATIC_TEST_ONLY else ("audit-future-1",)
        return JudgeAssessmentRecord(
            JudgeInputHasher.hash(self.judge_input), self.candidate.id, self.assessment,
            (self.evidence.id,), ("demand@0.1",), "opportunity.judge", "v0.1",
            runtime_id, runtime_version, audit_refs, source, "0.1", runtime_source=JudgeRuntimeSource.STATIC_ONLY if source is AssessmentRecordSource.STATIC_TEST_ONLY else JudgeRuntimeSource.LLM_RUNTIME,
        )

    def test_valid_record_is_immutable_and_versioned(self) -> None:
        record = self.record()
        self.assertEqual(record.record_version, "0.1")
        with self.assertRaises(FrozenInstanceError):
            record.runtime_id = "changed"  # type: ignore[misc]
        with self.assertRaises(ValueError):
            replace(record, record_version="v1")

    def test_validator_rejects_candidate_evidence_gate_and_input_hash_mismatch(self) -> None:
        other_assessment = replace(self.assessment, candidate_id="other")
        mismatches = (
            replace(self.record(), candidate_id="other", assessment=other_assessment),
            replace(self.record(), evidence_refs=("foreign-evidence",)),
            replace(self.record(), gate_refs=("foreign@0.1",)),
            replace(self.record(), judge_input_hash="0" * 64),
        )
        for record in mismatches:
            with self.assertRaises(ValueError):
                self.writer.append(record, self.judge_input)

    def test_append_only_store_persists_and_rejects_duplicate(self) -> None:
        record = self.record()
        self.writer.append(record, self.judge_input)
        self.assertEqual(self.store.get(record.assessment_id), record)
        self.assertEqual(self.store.list(), [record])
        with self.assertRaises(sqlite3.IntegrityError):
            self.writer.append(record, self.judge_input)
        self.assertFalse(hasattr(self.store, "update"))
        self.assertFalse(hasattr(self.store, "delete"))

    def test_write_boundary_accepts_declared_sources_and_rejects_unknown(self) -> None:
        static = self.record(AssessmentRecordSource.STATIC_TEST_ONLY)
        future = self.record(AssessmentRecordSource.FUTURE_JUDGE_RUNTIME)
        self.writer.append(static, self.judge_input)
        self.writer.append(future, self.judge_input)
        with self.assertRaises(ValueError):
            JudgeAssessmentRecord(
                JudgeInputHasher.hash(self.judge_input), self.candidate.id, self.assessment,
                (self.evidence.id,), ("demand@0.1",), "opportunity.judge", "v0.1",
                "runtime.unknown", "1.0", (), "UNKNOWN_CALLER", "0.1",  # type: ignore[arg-type]
            )

    def test_static_source_cannot_claim_runtime_and_future_source_needs_audit_ref(self) -> None:
        with self.assertRaises(ValueError):
            self.writer.append(replace(self.record(), runtime_id="runtime.fake"), self.judge_input)
        future = self.record(AssessmentRecordSource.FUTURE_JUDGE_RUNTIME)
        with self.assertRaises(ValueError):
            self.writer.append(replace(future, audit_refs=()), self.judge_input)

    def test_asset_layer_has_no_judge_runner_llm_triad_packet_consumer_builder_or_runtime_policy_dependencies(self) -> None:
        for path in (
            "opportunity/assessments/contracts.py",
            "opportunity/assessments/store.py",
            "opportunity/assessments/writer.py",
        ):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in (
                "opportunity.judge.runner", "governance", "opportunity.packets", "opportunity.consumers",
                "builders", "runtime.policy", "runtime.audit", "skills", "adapters", "crawlers",
            ):
                self.assertNotIn(forbidden, imports)
