"""Consumer access governance contracts, separate from Runtime Policy."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4
from .contracts import ConsumerAction, ConsumerAuditDecision, PacketReference
def now() -> str: return datetime.now(UTC).isoformat()
@dataclass(frozen=True, slots=True)
class ConsumerAccessRequest:
    consumer_id: str
    action: ConsumerAction
    packet_reference: PacketReference
    contract_version: str
    timestamp: str = field(default_factory=now)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self) -> None:
        if not self.request_id or not self.consumer_id or not self.contract_version or not self.timestamp: raise ValueError('access request fields are required')
        if self.action is not ConsumerAction.READ: raise ValueError('only READ access is permitted in v0.1')
@dataclass(frozen=True, slots=True)
class ConsumerAccessDecision:
    request_id: str
    consumer_id: str
    decision: ConsumerAuditDecision
    policy_id: str
    reason_code: str
    timestamp: str = field(default_factory=now)
@dataclass(frozen=True, slots=True)
class ConsumerPolicy:
    policy_id: str
    consumer_type: str
    allowed_actions: tuple[ConsumerAction, ...]
    allowed_packet_versions: tuple[str, ...]
    version: str
    def __post_init__(self) -> None:
        if not self.policy_id or not self.consumer_type or not self.version: raise ValueError('policy identity is required')
        if any(item is not ConsumerAction.READ for item in self.allowed_actions): raise ValueError('only READ policy actions are supported in v0.1')
        if not all(isinstance(item,str) and item for item in self.allowed_packet_versions): raise ValueError('policy packet versions are invalid')
