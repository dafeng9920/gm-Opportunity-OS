import ast
import unittest
from dataclasses import replace
from pathlib import Path

from candidates import CandidateRepository, EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from governance.triad.assembly import GovernanceTaskAssembler
from opportunity.assessments import (
    AssessmentRecordSource,
    AssessmentRecordWriter,
    JudgeAssessmentRecord,
    JudgeAssessmentStore,
    JudgeInputHasher,
)
from opportunity.gates.contracts import GateStatus, OpportunityGateResult, RuleResult
from opportunity.judge import AssessmentRecommendation, JudgeAssessment, JudgeInput


class GovernanceTaskAssemblyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"governance-task-assembly-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject("fixture", "signal", "https://example.test/evidence")
        self.ledger.append(self.evidence)
        self.candidates = CandidateRepository(self.database)
        self.candidate = CandidatePacket("Fixture", "signal", (self.evidence.id,), "fixture", 0.5)
        self.candidates.create(self.candidate)
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
        self.assembler = GovernanceTaskAssembler(
            self.store, self.candidates, EvidenceReferenceValidator(self.ledger)
        )

    def record(self, source: AssessmentRecordSource = AssessmentRecordSource.STATIC_TEST_ONLY) -> JudgeAssessmentRecord:
        static = source is AssessmentRecordSource.STATIC_TEST_ONLY
        return JudgeAssessmentRecord(
            JudgeInputHasher.hash(self.judge_input), self.candidate.id, self.assessment,
            (self.evidence.id,), ("demand@0.1",), "opportunity.judge", "v0.1",
            "STATIC_ONLY" if static else "runtime.future-judge", "STATIC_ONLY" if static else "1.0",
            () if static else ("audit-future-1",), source, "0.1",
        )

    def test_assembles_validated_task_from_persisted_runtime_record(self) -> None:
        record = self.record(AssessmentRecordSource.FUTURE_JUDGE_RUNTIME)
        self.writer.append(record, self.judge_input)
        task = self.assembler.assemble(record.assessment_id, task_id="governance-1")
        self.assertEqual(task.candidate_id, self.candidate.id)
        self.assertEqual(task.input_refs, (record.assessment_id,))
        self.assertEqual(task.metadata["judge_input_hash"], record.judge_input_hash)

    def test_rejects_missing_record_and_static_record_without_explicit_test_mode(self) -> None:
        with self.assertRaises(KeyError):
            self.assembler.assemble("missing", task_id="governance-1")
        record = self.record()
        self.writer.append(record, self.judge_input)
        with self.assertRaises(PermissionError):
            self.assembler.assemble(record.assessment_id, task_id="governance-1")
        self.assertEqual(
            self.assembler.assemble(record.assessment_id, task_id="governance-test", test_mode=True).candidate_id,
            self.candidate.id,
        )

    def test_rejects_candidate_and_evidence_lineage_mismatch(self) -> None:
        record = self.record(AssessmentRecordSource.FUTURE_JUDGE_RUNTIME)
        forged = replace(record, evidence_refs=("foreign-evidence",))
        self.store.append(forged)  # Simulates an untrusted bypass of the controlled writer.
        with self.assertRaisesRegex(ValueError, "evidence lineage"):
            self.assembler.assemble(forged.assessment_id, task_id="governance-1")

    def test_assembly_boundary_does_not_dispatch_triad_or_construct_snapshots(self) -> None:
        tree = ast.parse(Path("governance/triad/assembly.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("governance.triad.dispatch", "governance.triad.boundary", "opportunity.packets", "runtime", "skills"):
            self.assertNotIn(forbidden, imports)