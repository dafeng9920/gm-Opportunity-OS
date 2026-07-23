import tempfile
import unittest
from pathlib import Path

from architecture import ArchitectureEngine
from core.contracts import ContractRegistration, ContractRegistry
from core.lifecycle import ComponentLifecycleLedger
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component, RuntimeRegistration
from runtime.audit import AuditEvent, AuditLog


class ArchitectureEngineTests(unittest.TestCase):
    def fixture(self, directory: Path) -> ArchitectureEngine:
        database = directory / "architecture.db"
        registry = ComponentRegistry(database)
        registry.register(Component("agent.hermes", "Hermes Agent", "agent", "2026.7.20", "inactive", "waiting for runtime"))
        registry.register(Component("adapter.scrapling", "Scrapling Adapter", "adapter", "0.1.0", "active", "controlled crawler adapter"))
        registry.register(Component("runtime.scrapling-venv", "Scrapling Runtime", "runtime", "0.4.11", "active", "pinned subprocess runtime"))
        registry.register(Component("engine.opportunity-gates", "Opportunity Gate Engine", "skill", "0.1", "implemented", "deterministic candidate admission rules"))
        registry.register(Component("agent.opportunity-judge", "Opportunity Judge Agent", "agent", "0.1", "implemented", "interprets supplied candidate, evidence, and gate results"))
        registry.register(Component("plugin.roblox-opportunity", "Roblox Opportunity Plugin", "domain-plugin", "0.1", "implemented", "structured Roblox opportunity assessment rules"))
        registry.register(Component("adapter.youtube-signal", "YouTube RSS Signal Adapter", "adapter", "0.1", "active", "public channel RSS to signal discovery"))
        registry.register(Component("source.youtube", "YouTube", "data_source", "rss-v1", "active", "restricted public channel signal source"))
        registry.register_adapter(AdapterRegistration("adapter.scrapling", "scrapling@0.4.11", "0.1.0", "restricted-v0", "crawler.v0", "active"))
        registry.register_runtime(RuntimeRegistration("runtime.scrapling-venv", "scrapling-venv", "subprocess", "0.4.11", "restricted-v0", "available"))
        ContractRegistry(database).register(ContractRegistration("crawler.v0", "0.1", "external -> evidence", "discovery records enter Core"))
        lifecycle = ComponentLifecycleLedger(database)
        for state in ("EVALUATED", "SOURCE_ACQUIRED", "STATIC_REVIEWED", "WAITING_RUNTIME"):
            lifecycle.advance("agent.hermes", state, f"evidence-{state}")
        AuditLog(database).append(AuditEvent("adapter.scrapling", "adapter.scrapling", "runtime.scrapling-venv", "input", "output", "ALLOW", "scrapling@0.4.11", 1))
        return ArchitectureEngine(database)

    def test_renders_facts_lifecycle_and_runtime_without_plans(self) -> None:
        directory = Path(".opportunity-os") / "architecture-test"
        directory.mkdir(parents=True, exist_ok=True)
        database = directory / "architecture.db"
        if database.exists():
            database.unlink()
        engine = self.fixture(directory)
        fact = engine.fact_architecture()
        lifecycle = engine.lifecycle_graph()
        runtime = engine.runtime_graph()
        self.assertIn("Hermes Agent", fact)
        self.assertIn("Opportunity Gate Engine", fact)
        self.assertIn("Opportunity Judge Agent", fact)
        self.assertIn("Roblox Opportunity Plugin", fact)
        self.assertIn("YouTube RSS Signal Adapter", fact)
        self.assertIn("implemented", fact)
        self.assertIn("crawler.v0", fact)
        self.assertIn("SOURCE_ACQUIRED", lifecycle)
        self.assertIn("WAITING_RUNTIME", lifecycle)
        self.assertIn("runtime.scrapling-venv", runtime)
        self.assertIn("Evidence Ledger", runtime)
        self.assertNotIn("Triad Governance", fact)






