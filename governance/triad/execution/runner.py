"""Deterministic, non-agent role checks for the first Triad execution chain."""

from __future__ import annotations

from governance.triad.contracts import Role

from .contracts import RoleInvocation, RoleResult, RoleResultStatus, TriadExecutionContext
from .role_audit import RoleExecutionAuditEvent, RoleExecutionAuditStore


class DeterministicRoleRunner:
    """Runs deterministic readiness checks only; it never makes an admission decision."""

    def __init__(self, audit_store: RoleExecutionAuditStore) -> None:
        self._audit_store = audit_store

    def run(self, context: TriadExecutionContext, invocation: RoleInvocation) -> RoleResult:
        self._validate_context(context, invocation)
        self._validate_role_prerequisite(context, invocation)
        artifact_ref = f"role-result:{context.execution_id}:{invocation.role.value}"
        summary = f"{invocation.role.value} deterministic checks passed"
        result_payload = {
            "execution_id": context.execution_id,
            "task_id": context.governance_task_id,
            "role": invocation.role.value,
            "artifact_ref": artifact_ref,
            "summary": summary,
        }
        event = RoleExecutionAuditEvent(
            context.execution_id,
            context.governance_task_id,
            invocation.role,
            self._audit_store.hash({"invocation": invocation}),
            self._audit_store.hash(result_payload),
            RoleResultStatus.COMPLETED.value,
        )
        self._audit_store.append(event)
        return RoleResult(
            context.execution_id,
            context.governance_task_id,
            invocation.role,
            RoleResultStatus.COMPLETED,
            summary,
            (artifact_ref,),
            (event.audit_id,),
            invocation.contract_version,
        )

    @staticmethod
    def _validate_context(context: TriadExecutionContext, invocation: RoleInvocation) -> None:
        if (
            invocation.execution_id != context.execution_id
            or invocation.governance_task_id != context.governance_task_id
            or invocation.candidate_id != context.candidate_id
            or invocation.assessment_id != context.assessment_id
        ):
            raise ValueError("role invocation does not match execution context")

    @staticmethod
    def _validate_role_prerequisite(context: TriadExecutionContext, invocation: RoleInvocation) -> None:
        execution_ref = f"role-result:{context.execution_id}:{Role.EXECUTION.value}"
        review_ref = f"role-result:{context.execution_id}:{Role.REVIEW.value}"
        if invocation.role is Role.EXECUTION:
            if context.assessment_id not in invocation.input_refs:
                raise ValueError("execution role requires assessment input")
        elif invocation.role is Role.REVIEW:
            if execution_ref not in invocation.input_refs:
                raise ValueError("review role requires execution artifact input")
        elif invocation.role is Role.COMPLIANCE:
            if review_ref not in invocation.input_refs:
                raise ValueError("compliance role requires review artifact input")