"""Consumer contracts only. They identify future asset consumers; they do not read packets."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4
def now() -> str: return datetime.now(UTC).isoformat()
class ConsumerType(StrEnum): HUMAN='HUMAN'; SERVICE='SERVICE'; AGENT='AGENT'; BUILDER='BUILDER'
class ConsumerAction(StrEnum): READ='READ'
class ConsumerAuditDecision(StrEnum): ALLOW='ALLOW'; DENY='DENY'; REVIEW_REQUIRED='REVIEW_REQUIRED'
@dataclass(frozen=True, slots=True)
class ConsumerIdentity:
    consumer_id: str
    consumer_type: ConsumerType
    version: str
    created_at: str = field(default_factory=now)
    def __post_init__(self) -> None:
        if not self.consumer_id or not self.version: raise ValueError('consumer id and version are required')
        if not isinstance(self.consumer_type, ConsumerType): raise ValueError('consumer type is invalid')
@dataclass(frozen=True, slots=True)
class ConsumerCapability:
    consumer_id: str
    allowed_actions: tuple[ConsumerAction, ...]
    allowed_packet_versions: tuple[str, ...]
    purpose: str
    version: str
    def __post_init__(self) -> None:
        if not self.consumer_id or not self.purpose or not self.version or not self.allowed_actions or not self.allowed_packet_versions: raise ValueError('capability fields are required')
        if any(item is not ConsumerAction.READ for item in self.allowed_actions): raise ValueError('only READ action is permitted in v0.1')
        if not all(isinstance(item, str) and item for item in self.allowed_packet_versions): raise ValueError('allowed packet versions are required')
@dataclass(frozen=True, slots=True)
class PacketReference:
    packet_id: str
    packet_version: str
    def __post_init__(self) -> None:
        if not self.packet_id or not self.packet_version: raise ValueError('packet reference is required')
@dataclass(frozen=True, slots=True)
class PacketReadRequest:
    consumer_id: str
    packet_reference: PacketReference
    requested_action: ConsumerAction
    contract_version: str
    timestamp: str = field(default_factory=now)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self) -> None:
        if not self.consumer_id or not self.contract_version or not self.timestamp or not self.request_id: raise ValueError('read request fields are required')
        if self.requested_action is not ConsumerAction.READ: raise ValueError('only READ requests are permitted in v0.1')
@dataclass(frozen=True, slots=True)
class ConsumerAuditEvent:
    consumer_id: str
    packet_id: str
    packet_version: str
    action: ConsumerAction
    decision: ConsumerAuditDecision
    timestamp: str = field(default_factory=now)
    def __post_init__(self) -> None:
        if not self.consumer_id or not self.packet_id or not self.packet_version or not self.timestamp: raise ValueError('consumer audit identity is required')
        if self.action is not ConsumerAction.READ: raise ValueError('only READ audit actions are permitted in v0.1')
        if not isinstance(self.decision, ConsumerAuditDecision): raise ValueError('consumer audit decision is invalid')
