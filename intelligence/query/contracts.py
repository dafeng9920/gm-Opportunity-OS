"""Query contract for deterministic source selection, not collector execution."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4
def now() -> str: return datetime.now(UTC).isoformat()
@dataclass(frozen=True, slots=True)
class SignalQuery:
    domain: str
    entities: tuple[str, ...]
    signal_types: tuple[str, ...]
    sources: tuple[str, ...] = ()
    time_window: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    query_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)
    def __post_init__(self) -> None:
        if not self.query_id or not self.domain or not self.signal_types or not self.created_at: raise ValueError("query id, domain, signal types, and timestamp are required")
        if not all(item for item in self.entities + self.signal_types + self.sources): raise ValueError("query fields cannot contain empty values")
        if not isinstance(self.filters, dict): raise ValueError("filters must be an object")
@dataclass(frozen=True, slots=True)
class CollectorExecutionPlan:
    query_id: str
    source_id: str
    adapter_id: str
    signal_types: tuple[str, ...]
    limitations: tuple[str, ...]
    query: SignalQuery
