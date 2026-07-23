"""Packet query and snapshot-response contracts for the internal read boundary."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from opportunity.packets.models import PacketLifecycle
def now() -> str: return datetime.now(UTC).isoformat()
@dataclass(frozen=True, slots=True)
class PacketQuery:
    domain: str = ''
    lifecycle_status: PacketLifecycle | None = None
    opportunity_id: str = ''
    version: str = ''
    limit: int = 20
    contract_version: str = '0.1'
@dataclass(frozen=True, slots=True)
class PacketSnapshot:
    opportunity_id: str
    version: str
    lifecycle_status: PacketLifecycle
    serialized_packet: str
@dataclass(frozen=True, slots=True)
class PacketReadResult:
    request_id: str
    packets: tuple[PacketSnapshot, ...]
    returned_count: int
    timestamp: str = field(default_factory=now)
    contract_version: str = '0.1'
    def __post_init__(self) -> None:
        if self.returned_count != len(self.packets): raise ValueError('returned count must match packet snapshots')
