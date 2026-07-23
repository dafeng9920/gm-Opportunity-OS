"""Build Architecture-as-Code Mermaid artifacts from a registry/ledger fixture only."""
from pathlib import Path

from architecture import ArchitectureEngine
from core.contracts import ContractRegistration, ContractRegistry
from core.lifecycle import ComponentLifecycleLedger
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component, RuntimeRegistration
from runtime.audit import AuditEvent, AuditLog


def main() -> None:
    artifacts = Path(".opportunity-os") / "architecture-flow"
    artifacts.mkdir(parents=True, exist_ok=True)
    database = artifacts / "architecture.db"
    if database.exists():
        database.unlink()
    registry = ComponentRegistry(database)
    registry.register(Component("agent.hermes", "Hermes Agent", "agent", "2026.7.20", "inactive", "source acquired; waiting runtime"))
    registry.register(Component("adapter.hermes", "Hermes Adapter", "adapter", "0.1.0", "active", "controlled agent adapter"))
    registry.register(Component("adapter.scrapling", "Scrapling Adapter", "adapter", "0.1.0", "active", "controlled crawler adapter"))
    registry.register(Component("runtime.scrapling-venv", "Scrapling Runtime", "runtime", "0.4.11", "active", "pinned experimental subprocess"))
    registry.register(Component("engine.opportunity-gates", "Opportunity Gate Engine", "skill", "0.1", "implemented", "deterministic candidate admission rules"))
    registry.register(Component("agent.opportunity-judge", "Opportunity Judge Agent", "agent", "0.1", "implemented", "interprets supplied candidate, evidence, and gate results"))
    registry.register(Component("plugin.roblox-opportunity", "Roblox Opportunity Plugin", "domain-plugin", "0.1", "implemented", "structured Roblox opportunity assessment rules"))
    registry.register(Component("adapter.youtube-signal", "YouTube RSS Signal Adapter", "adapter", "0.1", "active", "public channel RSS to signal discovery"))
    registry.register(Component("source.youtube", "YouTube", "data_source", "rss-v1", "active", "restricted public channel signal source"))
    registry.register_adapter(AdapterRegistration("adapter.youtube-signal", "scrapling@0.4.11", "0.1", "restricted-v0", "crawler.v0", "active"))
    registry.register_adapter(AdapterRegistration("adapter.hermes", "hermes-agent@2026.7.20", "0.1.0", "restricted-v0", "agent.v0", "active"))
    registry.register_adapter(AdapterRegistration("adapter.scrapling", "scrapling@0.4.11", "0.1.0", "restricted-v0", "crawler.v0", "active"))
    registry.register_runtime(RuntimeRegistration("runtime.scrapling-venv", "Scrapling Worker", "subprocess", "0.4.11", "restricted-v0", "available"))
    contracts = ContractRegistry(database)
    contracts.register(ContractRegistration("agent.v0", "0.1", "task -> result", "validated agent result"))
    contracts.register(ContractRegistration("crawler.v0", "0.1", "external -> evidence", "discovery records enter Core"))
    lifecycle = ComponentLifecycleLedger(database)
    for state in ("EVALUATED", "SOURCE_ACQUIRED", "STATIC_REVIEWED", "WAITING_RUNTIME"):
        lifecycle.advance("agent.hermes", state, f"evidence-{state}")
    AuditLog(database).append(AuditEvent("adapter.scrapling", "adapter.scrapling", "runtime.scrapling-venv", "fixture-input", "fixture-output", "ALLOW", "scrapling@0.4.11", 683))
    output = Path("docs") / "generated"
    ArchitectureEngine(database).write(output)
    print(f"Architecture artifacts generated: {output.resolve()}")


if __name__ == "__main__":
    main()







