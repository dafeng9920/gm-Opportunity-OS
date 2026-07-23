import unittest
from pathlib import Path

from crawlers import CrawlRequest, CrawlerContractRunner, DiscoveryRecord
from core.registry import ComponentRegistry
from core.schemas import Component
from evidence import EvidenceLedger


class MockCrawler:
    crawler_id = "crawler.mock"

    def crawl(self, request: CrawlRequest):
        return [DiscoveryRecord("record-1", request.source, "url", "https://example.test/raw", {"fixture": True})]


class CrawlerContractTests(unittest.TestCase):
    def database(self, name: str) -> Path:
        path = Path(".opportunity-os") / name
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            path.unlink()
        return path

    def test_registered_crawler_creates_traceable_evidence(self) -> None:
        database = self.database("crawler-registered.db")
        registry = ComponentRegistry(database)
        registry.register(Component("crawler.mock", "Mock crawler", "crawler", "0.1.0", "active", "contract verification"))
        ledger = EvidenceLedger(database)
        request = CrawlRequest(source="test-source", target="test-target")
        evidence = CrawlerContractRunner(registry, ledger).collect(MockCrawler(), request)
        self.assertEqual(len(evidence), 1)
        stored = ledger.get(evidence[0].id)
        self.assertEqual(stored.metadata["crawler_id"], "crawler.mock")  # type: ignore[union-attr]
        self.assertEqual(stored.metadata["crawl_request_id"], request.id)  # type: ignore[union-attr]

    def test_unregistered_crawler_is_rejected(self) -> None:
        database = self.database("crawler-unregistered.db")
        runner = CrawlerContractRunner(ComponentRegistry(database), EvidenceLedger(database))
        with self.assertRaises(KeyError):
            runner.collect(MockCrawler(), CrawlRequest(source="test", target="target"))
