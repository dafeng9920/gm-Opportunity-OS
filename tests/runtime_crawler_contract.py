"""Executable proof of the crawler acquisition boundary using a mock adapter only."""
from pathlib import Path

from crawlers import CrawlRequest, CrawlerContractRunner, DiscoveryRecord
from core.registry import ComponentRegistry
from core.schemas import Component
from evidence import EvidenceLedger


class MockCrawler:
    crawler_id = "crawler.contract-demo"

    def crawl(self, request: CrawlRequest):
        return [DiscoveryRecord("demo-record", request.source, "url", "https://example.test/crawler-contract")]


def main() -> None:
    artifact_dir = Path(".opportunity-os")
    artifact_dir.mkdir(exist_ok=True)
    database = artifact_dir / "crawler-contract.db"
    if database.exists():
        database.unlink()

    registry = ComponentRegistry(database)
    registry.register(Component(MockCrawler.crawler_id, "Crawler Contract Demo", "crawler", "0.1.0", "active", "acquires raw discoveries"))
    request = CrawlRequest(source="contract-demo", target="opaque-target")
    evidence = CrawlerContractRunner(registry, EvidenceLedger(database)).collect(MockCrawler(), request)

    assert len(evidence) == 1
    assert evidence[0].metadata["crawl_request_id"] == request.id
    print(f"Crawler contract verified: crawler={MockCrawler.crawler_id}, evidence={evidence[0].id}")


if __name__ == "__main__":
    main()
