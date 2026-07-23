from __future__ import annotations

from hashlib import sha256
from typing import Any, Protocol

from crawlers.contract import CrawlRequest, DiscoveryRecord

from .policy import CapabilityPolicy, RESTRICTED_POLICY


class ScraplingBackend(Protocol):
    """Minimal external surface; implementations receive no Core storage handles."""
    def fetch(self, target: str, parameters: dict[str, Any]) -> str: ...


class ScraplingAdapter:
    """Controlled crawler adapter; it only translates a fetched page into DiscoveryRecord."""
    crawler_id = "adapter.scrapling"

    def __init__(self, backend: ScraplingBackend, policy: CapabilityPolicy = RESTRICTED_POLICY) -> None:
        self._backend = backend
        self._policy = policy

    def crawl(self, request: CrawlRequest) -> list[DiscoveryRecord]:
        body = self._backend.fetch(request.target, dict(request.parameters))
        if not isinstance(body, str) or not body:
            raise ValueError("scrapling backend returned no raw response")
        return [DiscoveryRecord(
            external_id=sha256((request.target + body).encode("utf-8")).hexdigest(),
            source=request.source,
            source_type="web",
            raw_reference=request.target,
            metadata={"adapter_id": self.crawler_id, "body_hash": sha256(body.encode("utf-8")).hexdigest()},
        )]
