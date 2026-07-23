"""Immutable contracts for forming a Candidate from already-ledgered Evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from core.schemas import CandidatePacket


def now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class CandidateFormationRequest:
    """Human-assisted request to form a candidate from selected Evidence IDs."""

    domain: str
    entity: str
    evidence_ids: tuple[str, ...]
    created_by: str
    contract_version: str
    confidence: float = 0.5
    request_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value.strip() for value in (
            self.request_id, self.domain, self.entity, self.created_by,
            self.contract_version, self.timestamp,
        )):
            raise ValueError("candidate formation request identity is required")
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids or not all(isinstance(value, str) and value.strip() for value in self.evidence_ids):
            raise ValueError("candidate formation requires evidence ids")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("candidate formation evidence ids must be unique")
        if not isinstance(self.confidence, (int, float)) or not 0 <= self.confidence <= 1:
            raise ValueError("candidate formation confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class CandidateFormationResult:
    """Result of a validated Candidate creation; it contains no opportunity decision."""

    candidate_id: str
    candidate_packet: CandidatePacket
    evidence_verified: bool
    timestamp: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.timestamp:
            raise ValueError("candidate formation result identity is required")
        if self.candidate_id != self.candidate_packet.id:
            raise ValueError("candidate formation result must match candidate packet")
        if self.evidence_verified is not True:
            raise ValueError("candidate formation result requires verified evidence")

