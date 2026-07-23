from __future__ import annotations

from typing import Any, Protocol
from urllib.parse import urlparse

from adapters.hermes import AgentResult, AgentTask
from adapters.policy import CapabilityPolicy, RESTRICTED_POLICY
from runtime.manager import RuntimeManager
from runtime.policy import InvocationRequest


class AgentWorker(Protocol):
    def run(self, task: AgentTask, policy: CapabilityPolicy) -> AgentResult: ...


class FetchWorker(Protocol):
    def fetch(self, target: str, parameters: dict[str, Any]) -> str: ...


class SandboxedAgentRuntime:
    """Isolated runtime bridge injected into HermesAgentAdapter."""
    def __init__(self, manager: RuntimeManager, worker: AgentWorker, runtime_id: str = "runtime.mock-sandbox") -> None:
        self.manager = manager
        self.worker = worker
        self.runtime_id = runtime_id

    def run(self, task: AgentTask, policy: CapabilityPolicy) -> AgentResult:
        request = InvocationRequest("adapter.hermes", "adapter.hermes", self.runtime_id)
        payload = {"task_id": task.id, "instruction": task.instruction, "evidence_refs": task.evidence_refs}
        return self.manager.invoke(request, policy, payload, lambda: self.worker.run(task, policy))


class SandboxedFetchBackend:
    """Isolated runtime bridge injected into ScraplingAdapter."""
    def __init__(self, manager: RuntimeManager, worker: FetchWorker, runtime_id: str = "runtime.mock-sandbox", allowed_hosts: tuple[str, ...] = (), external_version: str = "", adapter_id: str = "adapter.scrapling") -> None:
        self.manager = manager
        self.worker = worker
        self.runtime_id = runtime_id
        self.allowed_hosts = allowed_hosts
        self.external_version = external_version
        self.adapter_id = adapter_id

    def fetch(self, target: str, parameters: dict[str, Any]) -> str:
        host = urlparse(target).hostname or ""
        network = "allowlisted" if self.allowed_hosts else "none"
        request = InvocationRequest(self.adapter_id, self.adapter_id, self.runtime_id, network=network, allowed_hosts=self.allowed_hosts, target_host=host, external_version=self.external_version)
        return self.manager.invoke(request, RESTRICTED_POLICY, {"target": target, "parameters": parameters}, lambda: self.worker.fetch(target, parameters))




