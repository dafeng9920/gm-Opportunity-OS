import unittest

from governance.triad.boundary import BoundaryViolation, TriadBoundaryValidator
from governance.triad.contracts import GateDecision, GateDecisionRecord, GovernanceTask, Role, RoleArtifact
from governance.triad.dispatch import TriadDispatchService


def task(scope: str = "admission") -> GovernanceTask:
    return GovernanceTask("gate-1", "assess evidence admission", ("evidence-1",), "gate decision", scope)


class TriadGovernanceTests(unittest.TestCase):
    def test_dispatch_is_contract_only(self):
        dispatch = TriadDispatchService().create(task())
        self.assertEqual(tuple(role.value for role in dispatch.roles), ("EXECUTION", "REVIEW", "COMPLIANCE"))
        self.assertEqual(dispatch.gate_outputs, ("ALLOW", "BLOCK", "REVIEW_REQUIRED"))

    def test_checklist_blocks_missing_inputs_and_execution_scope(self):
        with self.assertRaises(ValueError):
            TriadDispatchService().create(GovernanceTask("", "crawl a source", (), "", "crawl"))

    def test_review_cannot_replace_execution(self):
        validator = TriadBoundaryValidator()
        with self.assertRaisesRegex(BoundaryViolation, "requires a formal Execution"):
            validator.accept_artifact(task(), RoleArtifact("gate-1", Role.REVIEW, "review"), ())

    def test_compliance_cannot_replace_review_or_decide_business_direction(self):
        validator = TriadBoundaryValidator()
        execution = RoleArtifact("gate-1", Role.EXECUTION, "execution")
        with self.assertRaisesRegex(BoundaryViolation, "requires a formal Review"):
            validator.accept_artifact(task(), RoleArtifact("gate-1", Role.COMPLIANCE, "compliance"), (execution,))
        with self.assertRaisesRegex(BoundaryViolation, "business direction"):
            validator.validate_task(task("business_direction"))

    def test_execution_cannot_issue_allow_and_complete_chain_can(self):
        validator = TriadBoundaryValidator()
        artifacts = (
            RoleArtifact("gate-1", Role.EXECUTION, "execution"),
            RoleArtifact("gate-1", Role.REVIEW, "review"),
            RoleArtifact("gate-1", Role.COMPLIANCE, "compliance"),
        )
        with self.assertRaisesRegex(BoundaryViolation, "only Compliance"):
            validator.issue_gate(task(), GateDecisionRecord("gate-1", GateDecision.ALLOW, "no", Role.EXECUTION), artifacts)
        validator.issue_gate(task(), GateDecisionRecord("gate-1", GateDecision.REVIEW_REQUIRED, "more evidence"), artifacts)
