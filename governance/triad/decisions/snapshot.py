"""Creates packet-facing snapshots only from persisted decision artifacts."""

from __future__ import annotations

from opportunity.packets.models import GovernanceSnapshot

from .contracts import DecisionArtifactSource
from .store import TriadDecisionStore


class GovernanceSnapshotFactory:
    def __init__(self, store: TriadDecisionStore) -> None:
        self._store = store

    def create(self, decision_artifact_id: str, *, test_mode: bool = False) -> GovernanceSnapshot:
        artifact = self._store.get(decision_artifact_id)
        if artifact is None:
            raise KeyError(f"decision artifact not found: {decision_artifact_id}")
        if artifact.source is DecisionArtifactSource.STATIC_TEST_ONLY and not test_mode:
            raise PermissionError("static-only decision artifacts require explicit test mode")
        return GovernanceSnapshot("REVIEWED", artifact.decision.decision, artifact.audit_refs, artifact.decision_artifact_id, artifact.candidate_id, artifact.assessment_id)