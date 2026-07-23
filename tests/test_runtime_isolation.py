import unittest
from pathlib import Path

from adapters import AgentResult, AgentTask, HermesAgentAdapter, RESTRICTED_POLICY, ScraplingAdapter
from agents import AgentContractRunner
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component, RuntimeRegistration
from crawlers import CrawlRequest, CrawlerContractRunner
from evidence import EvidenceLedger
from runtime import AuditLog, RuntimeManager
from runtime.bridges import SandboxedAgentRuntime, SandboxedFetchBackend
from runtime.policy import InvocationRequest


class MockAgentWorker:
    def run(self, task: AgentTask, policy):
        return AgentResult(task.id, "sandboxed result", task.evidence_refs, 0.9)


class MockFetchWorker:
    def fetch(self, target: str, parameters: dict[str, object]) -> str:
        return "<html>isolated fixture</html>"


class RuntimeIsolationTests(unittest.TestCase):
    def database(self) -> Path:
        path = Path(".opportunity-os") / "runtime-isolation.db"
        path.parent.mkdir(exist_ok=True)
        if path.exists():
            path.unlink()
        return path

    def setUp(self) -> None:
        self.database_path = self.database()
        self.registry = ComponentRegistry(self.database_path)
        self.audit = AuditLog(self.database_path)
        self.manager = RuntimeManager(self.registry, self.audit)
        self.registry.register(Component("runtime.mock-sandbox", "Mock Sandbox", "runtime", "0.1.0", "active", "mock isolated execution"))
        self.registry.register_runtime(RuntimeRegistration("runtime.mock-sandbox", "mock-sandbox", "sandbox", "0.1.0", "restricted-v0", "available"))

    def register_adapter(self, adapter_id: str, backend: str, contract: str) -> None:
        self.registry.register(Component(adapter_id, adapter_id, "adapter", "0.1.0", "active", "controlled adapter"))
        self.registry.register_adapter(AdapterRegistration(adapter_id, backend, "0.1.0", "restricted-v0", contract, "active"))

    def test_scrapling_adapter_runs_inside_sandbox_before_evidence(self) -> None:
        self.register_adapter("adapter.scrapling", "scrapling@0.4.11", "crawler.v0")
        backend = SandboxedFetchBackend(self.manager, MockFetchWorker())
        evidence = CrawlerContractRunner(self.registry, EvidenceLedger(self.database_path)).collect(
            ScraplingAdapter(backend), CrawlRequest(source="fixture", target="https://example.test/runtime")
        )
        self.assertEqual(len(evidence), 1)
        event = self.audit.list()[-1]
        self.assertEqual(event.adapter_id, "adapter.scrapling")
        self.assertEqual(event.decision, "ALLOW")
        self.assertTrue(event.input_hash and event.output_hash)

    def test_hermes_adapter_runs_inside_sandbox_before_result_validation(self) -> None:
        self.register_adapter("adapter.hermes", "hermes-agent@2026.7.20", "agent.v0")
        adapter = HermesAgentAdapter(SandboxedAgentRuntime(self.manager, MockAgentWorker()))
        result = AgentContractRunner(self.registry).execute(adapter, AgentTask("return bounded result", ("evidence-1",)))
        self.assertEqual(result.result, "sandboxed result")
        event = self.audit.list()[-1]
        self.assertEqual(event.adapter_id, "adapter.hermes")
        self.assertEqual(event.decision, "ALLOW")

    def test_core_access_request_is_denied_and_audited(self) -> None:
        request = InvocationRequest("test", "adapter.none", "runtime.mock-sandbox", database_access=True)
        with self.assertRaises(PermissionError):
            self.manager.invoke(request, RESTRICTED_POLICY, {"x": 1}, lambda: {"never": "runs"})
        event = self.audit.list()[-1]
        self.assertEqual(event.decision, "DENY")
        self.assertEqual(event.output_hash, "")


