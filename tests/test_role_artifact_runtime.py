import ast
import sqlite3
import unittest
from pathlib import Path

from governance.triad.contracts import Role
from governance.triad.execution import (
    AuditReferenceValidator,
    DeterministicRoleRunner,
    RoleArtifactAssembler,
    RoleArtifactRuntime,
    RoleExecutionAuditStore,
    RoleInvocation,
    TriadExecutionContext,
)


class RoleArtifactRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"role-artifact-runtime-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.context = TriadExecutionContext("execution-1", "task-1", "candidate-1", "assessment-1", "0.1")
        self.audit = RoleExecutionAuditStore(self.database)
        self.runtime = RoleArtifactRuntime(
            DeterministicRoleRunner(self.audit),
            RoleArtifactAssembler(AuditReferenceValidator(self.audit)),
        )

    def invocation(self, role: Role, refs: tuple[str, ...]) -> RoleInvocation:
        return RoleInvocation("execution-1", "task-1", "candidate-1", "assessment-1", role, refs, "0.1")

    def test_deterministic_execution_review_compliance_chain_persists_audited_artifacts(self) -> None:
        execution = self.runtime.execute(self.context, self.invocation(Role.EXECUTION, ("assessment-1",)))
        review = self.runtime.execute(self.context, self.invocation(Role.REVIEW, execution.input_refs))
        compliance = self.runtime.execute(self.context, self.invocation(Role.COMPLIANCE, review.input_refs))
        self.assertEqual([item.role for item in (execution, review, compliance)], [Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE])
        self.assertEqual(len(self.audit.list()), 3)
        self.assertTrue(all(self.audit.get(item.audit_refs[0]) is not None for item in (execution, review, compliance)))
        self.assertTrue(all(self.audit.get(item.audit_refs[0]).input_hash for item in (execution, review, compliance)))
        self.assertTrue(all(self.audit.get(item.audit_refs[0]).output_hash for item in (execution, review, compliance)))

    def test_runner_rejects_skipped_order_and_context_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "review role"):
            self.runtime.execute(self.context, self.invocation(Role.REVIEW, ("assessment-1",)))
        with self.assertRaisesRegex(ValueError, "compliance role"):
            self.runtime.execute(self.context, self.invocation(Role.COMPLIANCE, ("assessment-1",)))
        wrong = TriadExecutionContext("other", "task-1", "candidate-1", "assessment-1", "0.1")
        with self.assertRaisesRegex(ValueError, "context"):
            self.runtime.execute(wrong, self.invocation(Role.EXECUTION, ("assessment-1",)))
        self.assertEqual(self.audit.list(), [])

    def test_role_audit_store_is_append_only(self) -> None:
        artifact = self.runtime.execute(self.context, self.invocation(Role.EXECUTION, ("assessment-1",)))
        event = self.audit.get(artifact.audit_refs[0])
        self.assertIsNotNone(event)
        with self.assertRaises(sqlite3.IntegrityError):
            self.audit.append(event)
        self.assertFalse(hasattr(self.audit, "update"))
        self.assertFalse(hasattr(self.audit, "delete"))

    def test_runtime_boundary_has_no_agent_llm_runtime_manager_dispatch_or_decision_writer_dependencies(self) -> None:
        for path in (
            "governance/triad/execution/runner.py",
            "governance/triad/execution/runtime.py",
            "governance/triad/execution/role_audit.py",
        ):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ("runtime.manager", "governance.triad.dispatch", "governance.triad.decisions", "agents", "adapters", "skills", "opportunity.judge"):
                self.assertNotIn(forbidden, imports)