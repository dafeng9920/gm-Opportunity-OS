"""Validates persisted Decision Artifacts before materializing derived packet snapshots."""

from __future__ import annotations

from governance.triad.contracts import Role
from governance.triad.execution.audit import AuditReferenceValidator

from .contracts import DecisionArtifactSource, TriadDecisionArtifact
from .snapshot import GovernanceSnapshotFactory
from .store import TriadDecisionStore


class GovernanceSnapshotRuntime:
    """Derives a Snapshot from a persisted Decision Artifact; it never becomes a truth source."""

    def __init__(
        self,
        store: TriadDecisionStore,
        audit_validator: AuditReferenceValidator,
        factory: GovernanceSnapshotFactory | None = None,
    ) -> None:
        self._store = store
        self._audit_validator = audit_validator
        self._factory = factory or GovernanceSnapshotFactory(store)

    def materialize(self, artifact: TriadDecisionArtifact, *, test_mode: bool = False):
        persisted = self._store.get(artifact.decision_artifact_id)
        if persisted is None or persisted != artifact:
            raise ValueError("decision artifact must exist unchanged in append-only store")
        if artifact.source is DecisionArtifactSource.STATIC_TEST_ONLY and not test_mode:
            raise PermissionError("static-only decision artifacts require explicit test mode")
        self._validate_artifact(artifact)
        return self._factory.create(artifact.decision_artifact_id, test_mode=test_mode)

    def _validate_artifact(self, artifact: TriadDecisionArtifact) -> None:
        expected_roles = (Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE)
        if tuple(item.role for item in artifact.role_artifacts) != expected_roles:
            raise ValueError("decision artifact role artifacts must be complete and ordered")
        if artifact.decision.task_id != artifact.task_id:
            raise ValueError("decision artifact decision does not match task")
        flattened_audit_refs = tuple(ref for item in artifact.role_artifacts for ref in item.audit_refs)
        if artifact.audit_refs != flattened_audit_refs:
            raise ValueError("decision artifact audit references do not match role artifacts")
        for item in artifact.role_artifacts:
            if (
                not item.formal
                or item.task_id != artifact.task_id
                or item.candidate_id != artifact.candidate_id
                or item.assessment_id != artifact.assessment_id
                or not item.execution_id
            ):
                raise ValueError("decision artifact role artifact lineage is invalid")
            self._audit_validator.validate(item.audit_refs)