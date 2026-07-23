import unittest
from pathlib import Path

from core.lifecycle import ComponentLifecycleLedger


class ComponentLifecycleTests(unittest.TestCase):
    def ledger(self) -> ComponentLifecycleLedger:
        path = Path(".opportunity-os") / "lifecycle-test.db"
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            path.unlink()
        return ComponentLifecycleLedger(path)

    def test_hermes_waits_for_runtime_after_static_review(self) -> None:
        ledger = self.ledger()
        for state in ("EVALUATED", "SOURCE_ACQUIRED", "STATIC_REVIEWED", "WAITING_RUNTIME"):
            ledger.advance("agent.hermes", state, f"evidence-{state}")
        self.assertEqual(ledger.current("agent.hermes"), "WAITING_RUNTIME")

    def test_waiting_runtime_cannot_become_active(self) -> None:
        ledger = self.ledger()
        for state in ("EVALUATED", "SOURCE_ACQUIRED", "STATIC_REVIEWED", "WAITING_RUNTIME"):
            ledger.advance("agent.hermes", state, f"evidence-{state}")
        with self.assertRaises(ValueError):
            ledger.advance("agent.hermes", "ACTIVE", "evidence-active")
