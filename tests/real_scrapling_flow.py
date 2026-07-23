"""Experimental Phase 6 proof using the pinned Scrapling subprocess runtime."""
from pathlib import Path

from adapters import ScraplingAdapter
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component, RuntimeRegistration
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from runtime import AuditLog, RuntimeManager
from runtime.bridges import SandboxedFetchBackend
from runtime.real_workers import SubprocessScraplingWorker


def main() -> None:
    root = Path(".opportunity-os")
    root.mkdir(exist_ok=True)
    database = root / "phase6-scrapling.db"
    if database.exists():
        database.unlink()
    registry = ComponentRegistry(database)
    registry.register(Component("runtime.scrapling-venv", "Scrapling Experimental Runtime", "runtime", "0.4.11", "active", "isolated pinned Scrapling subprocess"))
    registry.register_runtime(RuntimeRegistration("runtime.scrapling-venv", "scrapling-venv", "subprocess", "0.4.11", "restricted-v0", "available"))
    registry.register(Component("adapter.scrapling", "Scrapling Adapter", "adapter", "0.1.0", "active", "controlled crawler adapter"))
    registry.register_adapter(AdapterRegistration("adapter.scrapling", "scrapling@0.4.11", "0.1.0", "restricted-v0", "crawler.v0", "active"))
    audit = AuditLog(database)
    worker = SubprocessScraplingWorker(root / "venvs" / "scrapling" / "Scripts" / "python.exe", Path("runtime/scrapling_worker.py"))
    backend = SandboxedFetchBackend(RuntimeManager(registry, audit), worker, "runtime.scrapling-venv", ("example.com",), "scrapling@0.4.11")
    evidence = CrawlerContractRunner(registry, EvidenceLedger(database)).collect(ScraplingAdapter(backend), CrawlRequest("phase6-example", "https://example.com/"))
    event = audit.list()[-1]
    assert event.decision == "ALLOW" and event.external_version == "scrapling@0.4.11" and event.output_hash
    print(f"Real Scrapling verified: evidence={evidence[0].id}, audit={event.id}, duration_ms={event.execution_ms}, output_hash={event.output_hash}")


if __name__ == "__main__":
    main()
