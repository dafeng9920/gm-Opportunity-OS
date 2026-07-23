"""Static-only Hermes lifecycle proof; it never imports or executes Hermes source."""
from pathlib import Path

from core.lifecycle import ComponentLifecycleLedger
from core.registry import ComponentRegistry
from core.schemas import Component, EvidenceObject
from evidence import EvidenceLedger


def main() -> None:
    root = Path(".opportunity-os")
    root.mkdir(exist_ok=True)
    database = root / "hermes-lifecycle.db"
    if database.exists():
        database.unlink()
    registry = ComponentRegistry(database)
    registry.register(Component("agent.hermes", "Hermes Agent", "agent", "2026.7.20", "inactive", "source acquired; waiting for approved runtime"))
    evidence_ledger = EvidenceLedger(database)
    lifecycle = ComponentLifecycleLedger(database)
    for state in ("EVALUATED", "SOURCE_ACQUIRED", "STATIC_REVIEWED", "WAITING_RUNTIME"):
        evidence = EvidenceObject("hermes-lifecycle", "lifecycle-event", f"agent.hermes:{state}", {"component": "agent.hermes", "previous_state": lifecycle.current("agent.hermes") or "", "new_state": state})
        evidence_ledger.append(evidence)
        lifecycle.advance("agent.hermes", state, evidence.id)
    assert registry.get("agent.hermes").status == "inactive"  # type: ignore[union-attr]
    assert lifecycle.current("agent.hermes") == "WAITING_RUNTIME"
    print("Hermes lifecycle verified: component=agent.hermes, registry=inactive, lifecycle=WAITING_RUNTIME")


if __name__ == "__main__":
    main()
