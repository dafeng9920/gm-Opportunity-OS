"""Access-only policy decision: it never reads Packet content or invokes evaluators."""
from __future__ import annotations
from .contracts import ConsumerAuditDecision
from .policy_contracts import ConsumerAccessDecision, ConsumerAccessRequest, ConsumerPolicy
from .registry import ConsumerRegistry
class ConsumerPolicyGate:
    def __init__(self, registry: ConsumerRegistry, policy: ConsumerPolicy) -> None: self._registry=registry; self._policy=policy
    def decide(self, request: ConsumerAccessRequest, consumer_version: str) -> ConsumerAccessDecision:
        identity=self._registry.get_identity(request.consumer_id,consumer_version)
        capability=self._registry.get_capability(request.consumer_id,consumer_version)
        if identity is None or capability is None: return self._result(request,ConsumerAuditDecision.DENY,'UNKNOWN_CONSUMER')
        if identity.consumer_type.value != self._policy.consumer_type: return self._result(request,ConsumerAuditDecision.REVIEW_REQUIRED,'CONSUMER_TYPE_REVIEW')
        if request.action not in capability.allowed_actions or request.action not in self._policy.allowed_actions: return self._result(request,ConsumerAuditDecision.DENY,'ACTION_NOT_ALLOWED')
        version=request.packet_reference.packet_version
        if version not in capability.allowed_packet_versions or version not in self._policy.allowed_packet_versions: return self._result(request,ConsumerAuditDecision.DENY,'PACKET_VERSION_NOT_ALLOWED')
        return self._result(request,ConsumerAuditDecision.ALLOW,'ACCESS_ALLOWED')
    def _result(self, request: ConsumerAccessRequest, decision: ConsumerAuditDecision, reason: str) -> ConsumerAccessDecision:
        return ConsumerAccessDecision(request.request_id,request.consumer_id,decision,self._policy.policy_id,reason)
