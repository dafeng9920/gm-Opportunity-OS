"""Immutable governance decision assets; no Triad execution is implemented here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import re
from uuid import uuid4

from governance.triad.contracts import GateDecisionRecord, RoleArtifact


def now() -> str:
    return datetime.now(UTC).isoformat()


class DecisionArtifactSource(StrEnum):
    DETERMINISTIC_TRIAD_RUNTIME = "DETERMINISTIC_TRIAD_RUNTIME"
    FUTURE_TRIAD_RUNTIME = "FUTURE_TRIAD_RUNTIME"
    STATIC_TEST_ONLY = "STATIC_TEST_ONLY"


@dataclass(frozen=True, slots=True)
class TriadDecisionArtifact:
    """Append-only provenance around a validated Triad decision."""

    task_id: str
    candidate_id: str
    assessment_id: str
    decision: GateDecisionRecord
    role_artifacts: tuple[RoleArtifact, ...]
    audit_refs: tuple[str, ...]
    source: DecisionArtifactSource
    artifact_version: str
    decision_artifact_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        required = (
            self.task_id, self.candidate_id, self.assessment_id, self.artifact_version,
            self.decision_artifact_id, self.created_at,
        )
        if not all(isinstance(item, str) and item.strip() for item in required):
            raise ValueError("decision artifact identity is required")
        if not re.fullmatch(r"\d+\.\d+", self.artifact_version):
            raise ValueError("decision artifact version must be major.minor")
        if not isinstance(self.decision, GateDecisionRecord):
            raise ValueError("decision artifact requires GateDecisionRecord")
        if not isinstance(self.source, DecisionArtifactSource):
            raise ValueError("decision artifact source is invalid")
        if not isinstance(self.role_artifacts, tuple):
            raise ValueError("role artifacts must be immutable")
        if not isinstance(self.audit_refs, tuple) or not all(isinstance(ref, str) and ref.strip() for ref in self.audit_refs):
            raise ValueError("audit references must be immutable strings")
        if len(set(self.audit_refs)) != len(self.audit_refs):
            raise ValueError("audit references must be unique")