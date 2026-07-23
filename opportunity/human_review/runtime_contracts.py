"""Runtime-only Human Review contracts; never Opportunity Packet lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from opportunity.consumers.contracts import PacketReference


def now() -> str:
    return datetime.now(UTC).isoformat()


class HumanReviewSessionStatus(StrEnum):
    OPEN = "OPEN"
    SUBMITTED = "SUBMITTED"
    CLOSED = "CLOSED"


class HumanReviewAuditAction(StrEnum):
    ACCESS_REQUESTED = "ACCESS_REQUESTED"
    PACKET_READ = "PACKET_READ"
    SESSION_CREATED = "SESSION_CREATED"
    DECISION_SUBMITTED = "DECISION_SUBMITTED"
    SESSION_CLOSED = "SESSION_CLOSED"


@dataclass(frozen=True, slots=True)
class HumanReviewSession:
    """Temporary review runtime state, separate from Opportunity Packet state."""

    review_id: str
    consumer_id: str
    packet_reference: PacketReference
    version: str
    status: HumanReviewSessionStatus = HumanReviewSessionStatus.OPEN
    session_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.session_id or not self.review_id or not self.consumer_id or not self.version:
            raise ValueError("human review session identity is required")
        if not self.created_at or not self.updated_at:
            raise ValueError("human review session timestamps are required")
        if not isinstance(self.status, HumanReviewSessionStatus):
            raise ValueError("human review session status is invalid")


@dataclass(frozen=True, slots=True)
class HumanReviewSessionEvent:
    session_id: str
    review_id: str
    status: HumanReviewSessionStatus
    timestamp: str = field(default_factory=now)


@dataclass(frozen=True, slots=True)
class HumanReviewAuditEvent:
    review_id: str
    consumer_id: str
    packet_id: str
    action: HumanReviewAuditAction
    decision: str
    timestamp: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.review_id or not self.consumer_id or not self.packet_id or not self.decision or not self.timestamp:
            raise ValueError("human review audit fields are required")
        if not isinstance(self.action, HumanReviewAuditAction):
            raise ValueError("human review audit action is invalid")
