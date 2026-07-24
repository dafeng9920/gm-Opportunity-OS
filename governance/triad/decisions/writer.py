"""Controlled write boundary for persisted Triad decision assets."""

from __future__ import annotations

from governance.triad.boundary import TriadBoundaryValidator
from governance.triad.contracts import GovernanceTask

from .contracts import DecisionArtifactSource, TriadDecisionArtifact
from .store import TriadDecisionStore


class TriadDecisionWriter:
    """Validates task lineage and role order; it does not execute a role or dispatch Triad."""

    def __init__(self, store: TriadDecisionStore, validator: TriadBoundaryValidator | None = None) -> None:
        self._store = store
        self._validator = validator or TriadBoundaryValidator()

    def append(self, artifact: TriadDecisionArtifact, task: GovernanceTask, *, test_mode: bool = False) -> None:
        if artifact.source is DecisionArtifactSource.STATIC_TEST_ONLY and not test_mode:
            raise PermissionError("static-only decision artifacts require explicit test mode")
        if artifact.task_id != task.id or artifact.decision.task_id != task.id:
            raise ValueError("decision artifact task does not match governance task")
        if not task.candidate_id or artifact.candidate_id != task.candidate_id:
            raise ValueError("decision artifact candidate does not match governance task")
        assessment_id = task.metadata.get("assessment_id")
        if not assessment_id or artifact.assessment_id != assessment_id or task.input_refs != (assessment_id,):
            raise ValueError("decision artifact assessment lineage does not match governance task")
        if artifact.source is not DecisionArtifactSource.STATIC_TEST_ONLY and not artifact.audit_refs:
            raise ValueError("runtime decision artifacts require audit references")
        self._validator.issue_gate(task, artifact.decision, artifact.role_artifacts)
        self._store.append(artifact)