"""Controlled handoff from audited RoleArtifacts to the existing Decision Writer."""

from __future__ import annotations

from governance.triad.contracts import GateDecisionRecord, GovernanceTask, Role, RoleArtifact
from governance.triad.execution import AuditReferenceValidator, TriadExecutionContext

from .contracts import DecisionArtifactSource, TriadDecisionArtifact
from .writer import TriadDecisionWriter


class TriadDecisionExecutionBoundary:
    """Persists a supplied decision only after complete, ordered, audited role execution."""

    def __init__(self, writer: TriadDecisionWriter, audit_validator: AuditReferenceValidator) -> None:
        self._writer = writer
        self._audit_validator = audit_validator

    def execute(
        self,
        task: GovernanceTask,
        context: TriadExecutionContext,
        role_artifacts: tuple[RoleArtifact, ...],
        decision: GateDecisionRecord,
    ) -> TriadDecisionArtifact:
        self._validate_task_context(task, context)
        self._validate_artifacts(context, role_artifacts)
        audit_refs = tuple(ref for artifact in role_artifacts for ref in artifact.audit_refs)
        artifact = TriadDecisionArtifact(
            task.id,
            context.candidate_id,
            context.assessment_id,
            decision,
            role_artifacts,
            audit_refs,
            DecisionArtifactSource.DETERMINISTIC_TRIAD_RUNTIME,
            "0.1",
        )
        self._writer.append(artifact, task)
        return artifact

    @staticmethod
    def _validate_task_context(task: GovernanceTask, context: TriadExecutionContext) -> None:
        if task.id != context.governance_task_id or task.candidate_id != context.candidate_id:
            raise ValueError("governance task does not match execution context")
        assessment_id = task.metadata.get("assessment_id")
        if not assessment_id or assessment_id != context.assessment_id or task.input_refs != (assessment_id,):
            raise ValueError("governance task assessment lineage does not match execution context")

    def _validate_artifacts(self, context: TriadExecutionContext, artifacts: tuple[RoleArtifact, ...]) -> None:
        expected_roles = (Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE)
        if not isinstance(artifacts, tuple) or tuple(artifact.role for artifact in artifacts) != expected_roles:
            raise ValueError("role artifacts must be complete and ordered execution review compliance")
        for artifact in artifacts:
            if (
                not artifact.formal
                or artifact.task_id != context.governance_task_id
                or artifact.execution_id != context.execution_id
                or artifact.candidate_id != context.candidate_id
                or artifact.assessment_id != context.assessment_id
            ):
                raise ValueError("role artifact lineage does not match execution context")
            self._audit_validator.validate(artifact.audit_refs)