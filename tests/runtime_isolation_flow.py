"""Executable mock-only proof: adapter -> runtime manager -> sandbox -> contract -> evidence."""
from pathlib import Path

from adapters import ScraplingAdapter
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component, RuntimeRegistration
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from runtime import AuditLog, RuntimeManager
from runtime.bridges import SandboxedFetchBackend


class MockWorker:
    def fetch(self, target: str, parameters: dict[str, object]) -> str:
        return "<html>runtime isolation proof</html>"


def main() -> None:
    directory = Path(".opportunity-os")
    directory.mkdir(exist_ok=True)
    database = directory / "runtime-isolation-flow.db"
    if database.exists():
        database.unlink()
    registry = ComponentRegistry(database)
    registry.register(Component("runtime.mock-sandbox", "Mock Sandbox", "runtime", "0.1.0", "active", "mock isolated execution"))
    registry.register_runtime(RuntimeRegistration("runtime.mock-sandbox", "mock-sandbox", "sandbox", "0.1.0", "restricted-v0", "available"))
    registry.register(Component("adapter.scrapling", "Scrapling Adapter", "adapter", "0.1.0", "active", "controlled crawler adapter"))
    registry.register_adapter(AdapterRegistration("adapter.scrapling", "scrapling@0.4.11", "0.1.0", "restricted-v0", "crawler.v0", "active"))
    audit = AuditLog(database)
    adapter = ScraplingAdapter(SandboxedFetchBackend(RuntimeManager(registry, audit), MockWorker()))
    evidence = CrawlerContractRunner(registry, EvidenceLedger(database)).collect(adapter, CrawlRequest("runtime-proof", "https://example.test/proof"))
    event = audit.list()[-1]
    assert event.decision == "ALLOW" and event.output_hash
    print(f"Runtime isolation verified: evidence={evidence[0].id}, audit={event.id}, decision={event.decision}")


if __name__ == "__main__":
    main()
