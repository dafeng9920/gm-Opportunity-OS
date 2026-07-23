"""Immutable Human Review contracts, independent from opportunity decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from opportunity.consumers.contracts import PacketReference


def now() -> str:
    return datetime.now(UTC).isoformat()


class HumanReviewDecisionType(StrEnum):
    """The limited outcomes a human reviewer may record."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"


@dataclass(frozen=True, slots=True)
class HumanReviewRequest:
    """A request for a registered human consumer to review a packet reference."""

    consumer_id: str
    packet_reference: PacketReference
    contract_version: str
    review_id: str = field(default_factory=lambda: str(uuid4()))
    request_timestamp: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.review_id or not self.consumer_id or not self.contract_version:
            raise ValueError("human review request identity is required")
        if not self.request_timestamp:
            raise ValueError("human review request timestamp is required")


@dataclass(frozen=True, slots=True)
class HumanReviewDecision:
    """A review-domain decision, never an Opportunity Packet lifecycle change."""

    review_id: str
    decision: HumanReviewDecisionType
    reviewer_id: str
    reason: str
    timestamp: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.review_id or not self.reviewer_id or not self.timestamp:
            raise ValueError("human review decision identity is required")
        if not isinstance(self.decision, HumanReviewDecisionType):
            raise ValueError("human review decision is invalid")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 1000:
            raise ValueError("human review reason must be non-empty text up to 1000 characters")


@dataclass(frozen=True, slots=True)
class HumanReviewRecord:
    """Immutable review evidence; it contains no packet content."""

    review_id: str
    consumer_id: str
    packet_reference: PacketReference
    decision: HumanReviewDecisionType
    reviewer_id: str
    reason: str
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.review_id or not self.consumer_id or not self.reviewer_id or not self.created_at:
            raise ValueError("human review record identity is required")
        if not isinstance(self.decision, HumanReviewDecisionType):
            raise ValueError("human review record decision is invalid")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 1000:
            raise ValueError("human review record reason must be non-empty text up to 1000 characters")
