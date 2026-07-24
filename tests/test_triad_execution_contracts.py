import ast
import unittest
from pathlib import Path

from governance.triad.contracts import Role
from governance.triad.execution import (
    AuditReferenceValidator,
    RoleArtifactAssembler,
    RoleInvocation,
    RoleResult,
    RoleResultStatus,
    TriadExecutionContext,
)


class FakeAuditLookup:
    def __init__(self, known: set[str]) -> None:
        self._known = known

    def get(self, audit_id: str) -> object | None:
        return audit_id if audit_id in self._known else None


class TriadExecutionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = TriadExecutionContext("execution-1", "task-1", "candidate-1", "assessment-1", "0.1")
        self.invocation = RoleInvocation(
            "execution-1", "task-1", "candidate-1", "assessment-1", Role.EXECUTION,
            ("assessment-1",), "0.1",
        )
        self.result = RoleResult(
            "execution-1", "task-1", Role.EXECUTION, RoleResultStatus.COMPLETED,
            "formal execution artifact", ("execution-output-1",), ("audit-1",), "0.1",
        )
        self.assembler = RoleArtifactAssembler(AuditReferenceValidator(FakeAuditLookup({"audit-1"})))

    def test_completed_result_with_real_audit_reference_becomes_formal_artifact(self) -> None:
        artifact = self.assembler.assemble(self.context, self.invocation, self.result)
        self.assertEqual(artifact.task_id, "task-1")
        self.assertEqual(artifact.role, Role.EXECUTION)
        self.assertEqual(artifact.input_refs, ("execution-output-1",))
        self.assertEqual(artifact.audit_refs, ("audit-1",))

    def test_context_result_and_audit_mismatches_are_rejected(self) -> None:
        wrong_context = TriadExecutionContext("other", "task-1", "candidate-1", "assessment-1", "0.1")
        with self.assertRaisesRegex(ValueError, "invocation"):
            self.assembler.assemble(wrong_context, self.invocation, self.result)
        unknown_audit = RoleResult(
            "execution-1", "task-1", Role.EXECUTION, RoleResultStatus.COMPLETED,
            "formal", (), ("unknown-audit",), "0.1",
        )
        with self.assertRaises(KeyError):
            self.assembler.assemble(self.context, self.invocation, unknown_audit)
        failed = RoleResult(
            "execution-1", "task-1", Role.EXECUTION, RoleResultStatus.FAILED,
            "failed", (), ("audit-1",), "0.1",
        )
        with self.assertRaisesRegex(ValueError, "completed"):
            self.assembler.assemble(self.context, self.invocation, failed)

    def test_contracts_reject_invalid_identity_role_and_reference_shapes(self) -> None:
        with self.assertRaises(ValueError):
            TriadExecutionContext("", "task-1", "candidate-1", "assessment-1", "0.1")
        with self.assertRaises(ValueError):
            RoleInvocation("execution-1", "task-1", "candidate-1", "assessment-1", Role.REVIEW, (), "0.1")
        with self.assertRaises(ValueError):
            RoleResult("execution-1", "task-1", Role.REVIEW, RoleResultStatus.COMPLETED, "summary", (), (), "v1")

    def test_execution_contract_layer_has_no_runtime_runner_agent_or_decision_writer_dependencies(self) -> None:
        for path in (
            "governance/triad/execution/contracts.py",
            "governance/triad/execution/audit.py",
            "governance/triad/execution/assembler.py",
        ):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ("runtime", "governance.triad.dispatch", "governance.triad.decisions", "skills", "adapters", "agents", "opportunity.packets"):
                self.assertNotIn(forbidden, imports)