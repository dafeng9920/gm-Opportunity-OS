from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4

from .policy import CapabilityPolicy, RESTRICTED_POLICY


def _required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class AgentTask:
    instruction: str
    evidence_refs: tuple[str, ...] = ()
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        _required(self.id, "id")
        _required(self.instruction, "instruction")
        if not all(isinstance(ref, str) and ref for ref in self.evidence_refs):
            raise ValueError("evidence_refs must contain non-empty strings")


@dataclass(frozen=True, slots=True)
class AgentResult:
    task_id: str
    result: str
    evidence_refs: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        _required(self.task_id, "task_id")
        _required(self.result, "result")
        if not all(isinstance(ref, str) and ref for ref in self.evidence_refs):
            raise ValueError("evidence_refs must contain non-empty strings")
        if not isinstance(self.confidence, (int, float)) or not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


class IsolatedAgentRuntime(Protocol):
    """A future runtime launcher; it has no Registry, Ledger, Queue, or database parameter."""
    def run(self, task: AgentTask, policy: CapabilityPolicy) -> AgentResult: ...


class HermesAgentAdapter:
    """Validates a bounded AgentResult from an injected isolated runtime."""
    agent_id = "adapter.hermes"

    def __init__(self, runtime: IsolatedAgentRuntime, policy: CapabilityPolicy = RESTRICTED_POLICY) -> None:
        self._runtime = runtime
        self._policy = policy

    def execute(self, task: AgentTask) -> AgentResult:
        result = self._runtime.run(task, self._policy)
        if not isinstance(result, AgentResult):
            raise ValueError("agent runtime returned an invalid result contract")
        if result.task_id != task.id:
            raise ValueError("agent result task_id does not match submitted task")
        if not set(result.evidence_refs).issubset(set(task.evidence_refs)):
            raise ValueError("agent result references evidence outside the submitted task")
        return result
