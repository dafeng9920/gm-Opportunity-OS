from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Iterable, Protocol
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class CrawlRequest:
    """Core-owned, business-neutral instruction supplied to a crawler adapter."""
    source: str
    target: str
    parameters: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    requested_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for name in ("id", "source", "target", "requested_at"):
            _non_empty(getattr(self, name), name)
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be an object")


@dataclass(frozen=True, slots=True)
class DiscoveryRecord:
    """Crawler-owned acquisition result before it becomes Core-owned evidence."""
    external_id: str
    source: str
    source_type: str
    raw_reference: str
    metadata: dict[str, Any] = field(default_factory=dict)
    captured_time: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for name in ("external_id", "source", "source_type", "raw_reference", "captured_time"):
            _non_empty(getattr(self, name), name)
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")


class CrawlerPort(Protocol):
    """Adapter contract: implementations acquire only, and never write Core storage."""
    crawler_id: str

    def crawl(self, request: CrawlRequest) -> Iterable[DiscoveryRecord]:
        """Return acquired raw discoveries for the supplied request."""
