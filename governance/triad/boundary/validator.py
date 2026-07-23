from __future__ import annotations

from governance.triad.contracts import GateDecisionRecord, GovernanceTask, Role, RoleArtifact


class BoundaryViolation(ValueError):
    pass


class TriadBoundaryValidator:
    """Enforces independent, ordered review and prevents role substitution."""

    def validate_task(self, task: GovernanceTask) -> None:
        if task.scope != "admission":
            raise BoundaryViolation("triad may govern admission only, never business direction")

    def accept_artifact(self, task: GovernanceTask, artifact: RoleArtifact, prior: tuple[RoleArtifact, ...]) -> None:
        self.validate_task(task)
        if artifact.task_id != task.id or not artifact.formal:
            raise BoundaryViolation("artifact must be formal and belong to the dispatched task")
        roles = {item.role for item in prior}
        if artifact.role is Role.EXECUTION:
            return
        if artifact.role is Role.REVIEW and Role.EXECUTION not in roles:
            raise BoundaryViolation("review requires a formal Execution artifact; it may not substitute execution")
        if artifact.role is Role.COMPLIANCE and Role.REVIEW not in roles:
            raise BoundaryViolation("compliance requires a formal Review artifact; it may not fill missing facts")

    def issue_gate(self, task: GovernanceTask, decision: GateDecisionRecord, prior: tuple[RoleArtifact, ...]) -> None:
        self.validate_task(task)
        if decision.task_id != task.id:
            raise BoundaryViolation("gate decision task mismatch")
        if decision.issued_by is not Role.COMPLIANCE:
            raise BoundaryViolation("only Compliance may issue a gate decision")
        roles = {item.role for item in prior}
        if not {Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE}.issubset(roles):
            raise BoundaryViolation("gate decision requires the complete formal triad chain")
