"""Non-authoritative proposal contracts for a future analysis layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from opportunity.evaluation import DEFAULT_GATE_FACT_REGISTRY


def now() -> str:
    return datetime.now(UTC).isoformat()


def _identity(value: str | None, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _references(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple) or not values or not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"{name} must be a non-empty immutable tuple of IDs")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must be unique")


class AnalysisProposalStatus(StrEnum):
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"


@dataclass(frozen=True, slots=True)
class AnalysisProposal:
    """An auditable suggestion; it has no Fact, Gate, Judge, or decision authority."""

    candidate_id: str
    measurement_artifact_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    requested_fact_id: str
    requested_fact_version: str
    analysis_summary: str
    assumptions: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    model_identity: str | None = None
    model_version: str | None = None
    runtime_identity: str | None = None
    prompt_reference_id: str | None = None
    status: AnalysisProposalStatus = AnalysisProposalStatus.NON_AUTHORITATIVE
    proposal_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        for value, name in (
            (self.proposal_id, "proposal_id"), (self.candidate_id, "candidate_id"),
            (self.requested_fact_id, "requested_fact_id"), (self.requested_fact_version, "requested_fact_version"),
            (self.analysis_summary, "analysis_summary"), (self.created_at, "created_at"),
        ):
            _identity(value, name)
        _references(self.measurement_artifact_ids, "measurement_artifact_ids")
        _references(self.evidence_ids, "evidence_ids")
        for values, name in ((self.assumptions, "assumptions"), (self.uncertainty, "uncertainty"), (self.missing_information, "missing_information")):
            if not isinstance(values, tuple) or not all(isinstance(value, str) and value.strip() for value in values):
                raise ValueError(f"{name} must be an immutable tuple of non-empty strings")
        for value, name in ((self.model_identity, "model_identity"), (self.model_version, "model_version"), (self.runtime_identity, "runtime_identity"), (self.prompt_reference_id, "prompt_reference_id")):
            _identity(value, name, optional=True)
        if (self.model_identity is None) != (self.model_version is None):
            raise ValueError("model identity and version must be provided together")
        if self.status is not AnalysisProposalStatus.NON_AUTHORITATIVE:
            raise ValueError("analysis proposal status must remain NON_AUTHORITATIVE")
        DEFAULT_GATE_FACT_REGISTRY.get(self.requested_fact_id, self.requested_fact_version)
