import ast
import unittest
from pathlib import Path
from types import MappingProxyType

from governance.triad.contracts import GateDecision, GateDecisionRecord, GovernanceTask, Role
from governance.triad.decisions import TriadDecisionExecutionBoundary, TriadDecisionStore, TriadDecisionWriter
from governance.triad.execution import (
    AuditReferenceValidator,
    DeterministicRoleRunner,
    RoleArtifactAssembler,
    RoleArtifactRuntime,
    RoleExecutionAuditStore,
    RoleInvocation,
    TriadExecutionContext,
)


class TriadDecisionExecutionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"triad-decision-execution-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.context = TriadExecutionContext("execution-1", "task-1", "candidate-1", "assessment-1", "0.1")
        self.task = GovernanceTask(
            "task-1", "govern admission", ("assessment-1",), "gate decision",
            metadata=MappingProxyType({"assessment_id": "assessment-1"}), candidate_id="candidate-1",
        )
        self.audit = RoleExecutionAuditStore(self.database)
        validator = AuditReferenceValidator(self.audit)
        self.role_runtime = RoleArtifactRuntime(DeterministicRoleRunner(self.audit), RoleArtifactAssembler(validator))
        self.boundary = TriadDecisionExecutionBoundary(TriadDecisionWriter(TriadDecisionStore(self.database)), validator)

    def invoke(self, role: Role, refs: tuple[str, ...]) -> RoleInvocation:
        return RoleInvocation("execution-1", "task-1", "candidate-1", "assessment-1", role, refs, "0.1")

    def artifacts(self):
        execution = self.role_runtime.execute(self.context, self.invoke(Role.EXECUTION, ("assessment-1",)))
        review = self.role_runtime.execute(self.context, self.invoke(Role.REVIEW, execution.input_refs))
        compliance = self.role_runtime.execute(self.context, self.invoke(Role.COMPLIANCE, review.input_refs))
        return execution, review, compliance

    def decision(self) -> GateDecisionRecord:
        return GateDecisionRecord("task-1", GateDecision.REVIEW_REQUIRED, "deterministic fixture", Role.COMPLIANCE)

    def test_complete_audited_role_chain_persists_deterministic_decision_artifact(self) -> None:
        artifact = self.boundary.execute(self.task, self.context, self.artifacts(), self.decision())
        self.assertEqual(artifact.source.value, "DETERMINISTIC_TRIAD_RUNTIME")
        self.assertEqual(artifact.candidate_id, "candidate-1")
        self.assertEqual(artifact.assessment_id, "assessment-1")
        self.assertEqual(len(artifact.audit_refs), 3)

    def test_missing_ordered_or_untrusted_artifacts_are_rejected(self) -> None:
        execution, review, compliance = self.artifacts()
        with self.assertRaisesRegex(ValueError, "complete and ordered"):
            self.boundary.execute(self.task, self.context, (execution, compliance), self.decision())
        with self.assertRaisesRegex(ValueError, "complete and ordered"):
            self.boundary.execute(self.task, self.context, (review, execution, compliance), self.decision())
        forged = type(compliance)(
            compliance.task_id, compliance.role, compliance.summary, compliance.formal, compliance.input_refs,
            ("missing-audit",), compliance.execution_id, compliance.candidate_id, compliance.assessment_id,
        )
        with self.assertRaises(KeyError):
            self.boundary.execute(self.task, self.context, (execution, review, forged), self.decision())

    def test_task_context_and_artifact_lineage_mismatches_are_rejected(self) -> None:
        execution, review, compliance = self.artifacts()
        wrong_task = GovernanceTask("other", "govern admission", ("assessment-1",), "gate decision", candidate_id="candidate-1")
        with self.assertRaisesRegex(ValueError, "task"):
            self.boundary.execute(wrong_task, self.context, (execution, review, compliance), self.decision())
        forged = type(compliance)(
            compliance.task_id, compliance.role, compliance.summary, compliance.formal, compliance.input_refs,
            compliance.audit_refs, compliance.execution_id, "other-candidate", compliance.assessment_id,
        )
        with self.assertRaisesRegex(ValueError, "lineage"):
            self.boundary.execute(self.task, self.context, (execution, review, forged), self.decision())

    def test_boundary_has_no_snapshot_packet_agent_or_runtime_manager_dependencies(self) -> None:
        tree = ast.parse(Path("governance/triad/decisions/execution.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("governance.triad.decisions.snapshot", "opportunity.packets", "runtime.manager", "agents", "adapters", "skills"):
            self.assertNotIn(forbidden, imports)