"""Validate Human Review contracts against Consumer identity, without reading packets."""

from __future__ import annotations

from opportunity.consumers.contracts import ConsumerType
from opportunity.consumers.registry import ConsumerRegistry

from .contracts import HumanReviewDecision, HumanReviewRecord, HumanReviewRequest


class HumanReviewValidator:
    """Validates human-consumer identity and turns a validated decision into a record."""

    def __init__(self, registry: ConsumerRegistry) -> None:
        self._registry = registry

    def validate_request(self, request: HumanReviewRequest, consumer_version: str) -> None:
        identity = self._registry.get_identity(request.consumer_id, consumer_version)
        if identity is None:
            raise KeyError("human review consumer is not registered")
        if identity.consumer_type is not ConsumerType.HUMAN:
            raise PermissionError("human review requires a HUMAN consumer")
        if request.contract_version != request.packet_reference.packet_version:
            raise ValueError("review contract version does not match packet version")

    def validate_decision(self, request: HumanReviewRequest, decision: HumanReviewDecision) -> None:
        if decision.review_id != request.review_id:
            raise ValueError("human review decision does not match request")
        if decision.reviewer_id != request.consumer_id:
            raise PermissionError("human review decision must be made by the requested consumer")

    def create_record(self, request: HumanReviewRequest, decision: HumanReviewDecision) -> HumanReviewRecord:
        self.validate_decision(request, decision)
        return HumanReviewRecord(
            review_id=request.review_id,
            consumer_id=request.consumer_id,
            packet_reference=request.packet_reference,
            decision=decision.decision,
            reviewer_id=decision.reviewer_id,
            reason=decision.reason,
            created_at=decision.timestamp,
        )
