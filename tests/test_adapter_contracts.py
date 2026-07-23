import unittest
from pathlib import Path

from adapters import AgentResult, AgentTask, CapabilityPolicy, HermesAgentAdapter, ScraplingAdapter
from agents import AgentContractRunner
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger


class MockScraplingBackend:
    def fetch(self, target: str, parameters: dict[str, object]) -> str:
        return "<html><title>fixture</title></html>"


class MockHermesRuntime:
    def __init__(self) -> None:
        self.policy = None

    def run(self, task: AgentTask, policy: CapabilityPolicy) -> AgentResult:
        self.policy = policy
        return AgentResult(task.id, "bounded mock result", task.evidence_refs, 0.8)


class AdapterContractTests(unittest.TestCase):
    def database(self, name: str) -> Path:
        path = Path(".opportunity-os") / name
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            path.unlink()
        return path

    def register_adapter(self, registry: ComponentRegistry, adapter_id: str, backend: str, contract: str) -> None:
        registry.register(Component(adapter_id, adapter_id, "adapter", "0.1.0", "active", "controlled adapter"))
        registry.register_adapter(AdapterRegistration(adapter_id, backend, "0.1.0", "restricted-v0", contract, "active"))

    def test_scrapling_adapter_flows_through_contract_to_evidence(self) -> None:
        database = self.database("adapter-scrapling.db")
        registry = ComponentRegistry(database)
        self.register_adapter(registry, "adapter.scrapling", "scrapling@0.4.11", "crawler.v0")
        adapter = ScraplingAdapter(MockScraplingBackend())
        evidence = CrawlerContractRunner(registry, EvidenceLedger(database)).collect(
            adapter, CrawlRequest(source="fixture-web", target="https://example.test/page")
        )
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].raw_reference, "https://example.test/page")
        self.assertEqual(evidence[0].metadata["crawler_id"], "adapter.scrapling")
        self.assertEqual(evidence[0].metadata["adapter_id"], "adapter.scrapling")

    def test_hermes_adapter_validates_bounded_result_in_isolated_chain(self) -> None:
        database = self.database("adapter-hermes.db")
        registry = ComponentRegistry(database)
        self.register_adapter(registry, "adapter.hermes", "hermes-agent@2026.7.20", "agent.v0")
        runtime = MockHermesRuntime()
        task = AgentTask("summarize supplied evidence", ("evidence-1",))
        result = AgentContractRunner(registry).execute(HermesAgentAdapter(runtime), task)
        self.assertEqual(result.task_id, task.id)
        self.assertEqual(runtime.policy.database, "no_direct_access")  # type: ignore[union-attr]
        self.assertEqual(runtime.policy.execution, "controlled")  # type: ignore[union-attr]

    def test_policy_rejects_direct_database_access(self) -> None:
        with self.assertRaises(ValueError):
            CapabilityPolicy(database="read_write")


class BadHermesRuntime:
    def run(self, task: AgentTask, policy: CapabilityPolicy) -> AgentResult:
        return AgentResult(task.id, "bad reference", ("outside-evidence",), 0.5)


class AdapterNegativeContractTests(unittest.TestCase):
    def test_hermes_rejects_evidence_not_present_in_task(self) -> None:
        task = AgentTask("summarize supplied evidence", ("evidence-1",))
        with self.assertRaises(ValueError):
            HermesAgentAdapter(BadHermesRuntime()).execute(task)
