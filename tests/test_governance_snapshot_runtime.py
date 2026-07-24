import ast
import unittest
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

from governance.triad.contracts import GateDecision, GateDecisionRecord, GovernanceTask, Role
from governance.triad.decisions import (
    GovernanceSnapshotRuntime,
    TriadDecisionExecutionBoundary,
    TriadDecisionStore,
    TriadDecisionWriter,
)
from governance.triad.execution import (
    AuditReferenceValidator,
    DeterministicRoleRunner,
    RoleArtifactAssembler,
    RoleArtifactRuntime,
    RoleExecutionAuditStore,
    RoleInvocation,
    TriadExecutionContext,
)


class GovernanceSnapshotRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"governance-snapshot-runtime-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.context = TriadExecutionContext("execution-1", "task-1", "candidate-1", "assessment-1", "0.1")
        self.task = GovernanceTask(
            "task-1", "govern admission", ("assessment-1",), "gate decision",
            metadata=MappingProxyType({"assessment_id": "assessment-1"}), candidate_id="candidate-1",
        )
        self.audit = RoleExecutionAuditStore(self.database)
        validator = AuditReferenceValidator(self.audit)
        runtime = RoleArtifactRuntime(DeterministicRoleRunner(self.audit), RoleArtifactAssembler(validator))
        execution = runtime.execute(self.context, RoleInvocation("execution-1", "task-1", "candidate-1", "assessment-1", Role.EXECUTION, ("assessment-1",), "0.1"))
        review = runtime.execute(self.context, RoleInvocation("execution-1", "task-1", "candidate-1", "assessment-1", Role.REVIEW, execution.input_refs, "0.1"))
        compliance = runtime.execute(self.context, RoleInvocation("execution-1", "task-1", "candidate-1", "assessment-1", Role.COMPLIANCE, review.input_refs, "0.1"))
        self.store = TriadDecisionStore(self.database)
        boundary = TriadDecisionExecutionBoundary(TriadDecisionWriter(self.store), validator)
        self.artifact = boundary.execute(
            self.task, self.context, (execution, review, compliance),
            GateDecisionRecord("task-1", GateDecision.REVIEW_REQUIRED, "fixture decision", Role.COMPLIANCE),
        )
        self.runtime = GovernanceSnapshotRuntime(self.store, validator)

    def test_persisted_decision_artifact_derives_validated_snapshot(self) -> None:
        snapshot = self.runtime.materialize(self.artifact)
        self.assertEqual(snapshot.decision_artifact_id, self.artifact.decision_artifact_id)
        self.assertEqual(snapshot.candidate_id, "candidate-1")
        self.assertEqual(snapshot.assessment_id, "assessment-1")
        self.assertEqual(snapshot.decision, GateDecision.REVIEW_REQUIRED)

    def test_rejects_unpersisted_tampered_and_audit_invalid_artifacts(self) -> None:
        tampered = replace(self.artifact, candidate_id="other-candidate")
        with self.assertRaisesRegex(ValueError, "unchanged"):
            self.runtime.materialize(tampered)
        bad_audit = replace(self.artifact, decision_artifact_id="bad-audit-artifact", audit_refs=("missing-audit",))
        self.store.append(bad_audit)
        with self.assertRaisesRegex(ValueError, "audit references"):
            self.runtime.materialize(bad_audit)

    def test_snapshot_runtime_has_no_packet_assembler_agent_or_runtime_manager_dependencies(self) -> None:
        tree = ast.parse(Path("governance/triad/decisions/snapshot_runtime.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertIn("governance.triad.execution.audit", imports)
        for forbidden in ("governance.triad.execution", "opportunity.packets.contracts", "runtime.manager", "agents", "adapters", "skills", "builders"):
            self.assertNotIn(forbidden, imports)