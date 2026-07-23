"""Composes Policy Gate and Consumer Audit Store. It does not call the Packet Reader."""
from __future__ import annotations
from .audit_store import ConsumerAuditStore
from .contracts import ConsumerAuditEvent
from .policy_contracts import ConsumerAccessDecision, ConsumerAccessRequest
from .policy_gate import ConsumerPolicyGate
class ConsumerAccessRuntime:
    def __init__(self, gate: ConsumerPolicyGate, audit: ConsumerAuditStore) -> None: self._gate=gate; self._audit=audit
    def decide(self, request: ConsumerAccessRequest, consumer_version: str) -> ConsumerAccessDecision:
        decision=self._gate.decide(request,consumer_version)
        self._audit.append(ConsumerAuditEvent(request.consumer_id,request.packet_reference.packet_id,request.packet_reference.packet_version,request.action,decision.decision))
        return decision
