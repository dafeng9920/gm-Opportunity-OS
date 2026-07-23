"""Governed Human Review runtime: policy access, snapshot read, session, record, audit."""

from __future__ import annotations

from opportunity.consumers import (
    ConsumerAccessRuntime,
    ConsumerAction,
    ConsumerAuditDecision,
    PacketQuery,
    PacketReadRequest,
)
from opportunity.consumers.policy_contracts import ConsumerAccessRequest
from opportunity.consumers.reader import OpportunityPacketReader
from opportunity.consumers.read_contracts import PacketSnapshot

from .audit_store import HumanReviewAuditStore
from .contracts import HumanReviewDecision, HumanReviewRecord, HumanReviewRequest
from .runtime_contracts import HumanReviewAuditAction, HumanReviewAuditEvent, HumanReviewSession
from .store import HumanReviewStore
from .validator import HumanReviewValidator


class HumanReviewRuntime:
    """Runs a review only after Consumer Policy allows a read; it never writes packets."""

    def __init__(
        self,
        validator: HumanReviewValidator,
        access: ConsumerAccessRuntime,
        reader: OpportunityPacketReader,
        store: HumanReviewStore,
        audit: HumanReviewAuditStore,
    ) -> None:
        self._validator = validator
        self._access = access
        self._reader = reader
        self._store = store
        self._audit = audit

    def start_review(self, request: HumanReviewRequest, consumer_version: str) -> tuple[HumanReviewSession, PacketSnapshot]:
        self._validator.validate_request(request, consumer_version)
        access = self._access.decide(
            ConsumerAccessRequest(
                request.consumer_id, ConsumerAction.READ, request.packet_reference, request.contract_version,
            ),
            consumer_version,
        )
        self._audit.append(
            HumanReviewAuditEvent(
                request.review_id, request.consumer_id, request.packet_reference.packet_id,
                HumanReviewAuditAction.ACCESS_REQUESTED, access.decision.value,
            )
        )
        if access.decision is not ConsumerAuditDecision.ALLOW:
            raise PermissionError(f"human review access denied: {access.reason_code}")
        read = self._reader.read(
            PacketReadRequest(
                request.consumer_id, request.packet_reference, ConsumerAction.READ, request.contract_version,
            ),
            consumer_version,
            PacketQuery(
                opportunity_id=request.packet_reference.packet_id,
                version=request.packet_reference.packet_version,
                limit=1,
            ),
        )
        if not read.packets:
            self._audit.append(
                HumanReviewAuditEvent(
                    request.review_id, request.consumer_id, request.packet_reference.packet_id,
                    HumanReviewAuditAction.PACKET_READ, "NOT_FOUND",
                )
            )
            raise KeyError("opportunity packet not found")
        snapshot = read.packets[0]
        self._audit.append(
            HumanReviewAuditEvent(
                request.review_id, request.consumer_id, request.packet_reference.packet_id,
                HumanReviewAuditAction.PACKET_READ, ConsumerAuditDecision.ALLOW.value,
            )
        )
        session = HumanReviewSession(
            request.review_id, request.consumer_id, request.packet_reference, request.contract_version,
        )
        self._store.create_session(session)
        self._audit.append(
            HumanReviewAuditEvent(
                request.review_id, request.consumer_id, request.packet_reference.packet_id,
                HumanReviewAuditAction.SESSION_CREATED, ConsumerAuditDecision.ALLOW.value,
            )
        )
        return session, snapshot

    def submit_decision(
        self,
        session_id: str,
        decision: HumanReviewDecision,
        consumer_version: str,
    ) -> HumanReviewRecord:
        session = self._store.get_session(session_id)
        if session is None:
            raise KeyError("human review session not found")
        request = HumanReviewRequest(
            session.consumer_id, session.packet_reference, session.version,
            session.review_id, session.created_at,
        )
        self._validator.validate_request(request, consumer_version)
        record = self._validator.create_record(request, decision)
        self._store.submit_decision(session_id, decision, record)
        self._audit.append(
            HumanReviewAuditEvent(
                session.review_id, session.consumer_id, session.packet_reference.packet_id,
                HumanReviewAuditAction.DECISION_SUBMITTED, decision.decision.value,
            )
        )
        self._store.close_session(session_id)
        self._audit.append(
            HumanReviewAuditEvent(
                session.review_id, session.consumer_id, session.packet_reference.packet_id,
                HumanReviewAuditAction.SESSION_CLOSED, ConsumerAuditDecision.ALLOW.value,
            )
        )
        return record
