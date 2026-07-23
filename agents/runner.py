from adapters.hermes import AgentResult, AgentTask, HermesAgentAdapter
from core.registry import ComponentRegistry


class AgentContractRunner:
    """Core-owned validation boundary for agent adapters; it does not mutate Core state."""
    def __init__(self, registry: ComponentRegistry) -> None:
        self.registry = registry

    def execute(self, adapter: HermesAgentAdapter, task: AgentTask) -> AgentResult:
        component = self.registry.get(adapter.agent_id)
        adapter_record = self.registry.get_adapter(adapter.agent_id)
        if component is None or component.type != "adapter" or component.status != "active":
            raise ValueError("agent adapter is not active")
        if adapter_record is None or adapter_record.status != "active" or adapter_record.contract != "agent.v0":
            raise ValueError("agent adapter is not contract-compatible")
        return adapter.execute(task)
