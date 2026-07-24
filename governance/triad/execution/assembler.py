"""Validation-only conversion from RoleResult to the existing RoleArtifact contract."""

from __future__ import annotations

from governance.triad.contracts import RoleArtifact

from .audit import AuditReferenceValidator
from .contracts import RoleInvocation, RoleResult, RoleResultStatus, TriadExecutionContext


class RoleArtifactAssembler:
    """Creates a formal RoleArtifact after context, result, and audit-reference validation."""

    def __init__(self, audit_validator: AuditReferenceValidator) -> None:
        self._audit_validator = audit_validator

    def assemble(
        self,
        context: TriadExecutionContext,
        invocation: RoleInvocation,
        result: RoleResult,
    ) -> RoleArtifact:
        if (
            invocation.execution_id != context.execution_id
            or invocation.governance_task_id != context.governance_task_id
            or invocation.candidate_id != context.candidate_id
            or invocation.assessment_id != context.assessment_id
        ):
            raise ValueError("role invocation does not match execution context")
        if (
            result.execution_id != context.execution_id
            or result.governance_task_id != context.governance_task_id
            or result.role is not invocation.role
        ):
            raise ValueError("role result does not match execution context or invocation")
        if result.status is not RoleResultStatus.COMPLETED:
            raise ValueError("only completed role results may become formal artifacts")
        self._audit_validator.validate(result.audit_refs)
        return RoleArtifact(
            task_id=context.governance_task_id,
            role=result.role,
            summary=result.summary,
            formal=True,
            input_refs=result.artifact_refs,
            audit_refs=result.audit_refs,
            execution_id=context.execution_id,
            candidate_id=context.candidate_id,
            assessment_id=context.assessment_id,
        )