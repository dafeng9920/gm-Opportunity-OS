from __future__ import annotations

from core.registry import ComponentRegistry
from core.schemas import EvidenceObject
from evidence import EvidenceLedger

from .contract import CrawlerPort, CrawlRequest


class CrawlerContractRunner:
    """Validates crawler or registered crawler-adapter output before writing Evidence."""
    def __init__(self, registry: ComponentRegistry, evidence_ledger: EvidenceLedger) -> None:
        self.registry = registry
        self.evidence_ledger = evidence_ledger

    def collect(self, crawler: CrawlerPort, request: CrawlRequest) -> list[EvidenceObject]:
        component = self.registry.get(crawler.crawler_id)
        if component is None:
            raise KeyError(f"crawler is not registered: {crawler.crawler_id}")
        if component.status != "active":
            raise ValueError(f"crawler is not active and usable: {crawler.crawler_id}")
        if component.type == "adapter":
            adapter = self.registry.get_adapter(crawler.crawler_id)
            if adapter is None or adapter.status != "active" or adapter.contract != "crawler.v0":
                raise ValueError(f"crawler adapter is not active and contract-compatible: {crawler.crawler_id}")
        elif component.type != "crawler":
            raise ValueError(f"crawler is not contract-compatible: {crawler.crawler_id}")

        evidence_items: list[EvidenceObject] = []
        for record in crawler.crawl(request):
            metadata = {
                **record.metadata,
                "crawler_id": crawler.crawler_id,
                "crawl_request_id": request.id,
                "external_id": record.external_id,
            }
            evidence = EvidenceObject(
                source=record.source,
                source_type=record.source_type,
                raw_reference=record.raw_reference,
                captured_time=record.captured_time,
                metadata=metadata,
            )
            self.evidence_ledger.append(evidence)
            evidence_items.append(evidence)
        return evidence_items
