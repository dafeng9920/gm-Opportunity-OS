import unittest
from pathlib import Path

from core.registry import ComponentRegistry
from core.schemas import Component


class RegistryTests(unittest.TestCase):
    def test_crud(self) -> None:
        database = Path(".opportunity-os") / "test-registry.db"
        database.parent.mkdir(exist_ok=True)
        if database.exists():
            database.unlink()
        registry = ComponentRegistry(database)
        component = Component("source.manual", "Manual source", "data_source", "0.1.0", "active", "manual signal capture")
        registry.register(component)
        self.assertEqual(registry.get(component.id), component)
        registry.update_status(component.id, "inactive")
        self.assertEqual(registry.get(component.id).status, "inactive")  # type: ignore[union-attr]
        registry.delete(component.id)
        self.assertIsNone(registry.get(component.id))
