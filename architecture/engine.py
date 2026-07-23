from __future__ import annotations

from pathlib import Path

from core.contracts import ContractRegistry
from core.lifecycle import ComponentLifecycleLedger
from core.registry import ComponentRegistry
from core.state import TRANSITIONS
from runtime.audit import AuditLog


def _node(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value)


class ArchitectureEngine:
    """Renders diagrams from registries/ledgers only; it never scans implementation code."""
    def __init__(self, database: Path | str) -> None:
        self.registry = ComponentRegistry(database)
        self.lifecycle = ComponentLifecycleLedger(database)
        self.contracts = ContractRegistry(database)
        self.audit = AuditLog(database)

    def fact_architecture(self) -> str:
        lines = ["flowchart LR", "  registry[(Component Registry)]", "  contracts[(Contract Registry)]"]
        for component in self.registry.list():
            node = _node(component.id)
            lines.append(f'  {node}["{component.name}\\n{component.type} - {component.status}"]')
            lines.append(f"  registry -.-> {node}")
        for adapter in self.registry.list_adapters():
            adapter_node = _node(adapter.adapter_id)
            backend = _node("backend_" + adapter.adapter_id)
            contract = _node("contract_" + adapter.contract)
            lines.append(f'  {backend}["{adapter.backend_component}\\nexternal backend"]')
            lines.append(f"  {adapter_node} --> {backend}")
            lines.append(f'  {contract}["{adapter.contract}"]')
            lines.append(f"  contracts -. declares .-> {contract}")
            lines.append(f"  {adapter_node} --> {contract}")
        for runtime in self.registry.list_runtimes():
            runtime_node = _node(runtime.runtime_id)
            policy = _node("policy_" + runtime.policy)
            lines.append(f'  {policy}["{runtime.policy}"]')
            lines.append(f"  {runtime_node} -. policy .-> {policy}")
        return "\n".join(dict.fromkeys(lines)) + "\n"

    def lifecycle_graph(self) -> str:
        lines = ["stateDiagram-v2"]
        for event in self.lifecycle.list():
            if event.previous_state:
                lines.append(f"  {event.previous_state} --> {event.new_state}: {event.component_id}")
            else:
                lines.append(f"  [*] --> {event.new_state}: {event.component_id}")
        return "\n".join(dict.fromkeys(lines)) + "\n"

    def runtime_graph(self) -> str:
        lines = ["flowchart LR", "  audit[(Runtime Audit)]"]
        adapters = {item.adapter_id: item for item in self.registry.list_adapters()}
        runtimes = {item.runtime_id: item for item in self.registry.list_runtimes()}
        for event in self.audit.list():
            runtime = _node(event.runtime_id)
            adapter = _node(event.adapter_id)
            runtime_record = runtimes.get(event.runtime_id)
            runtime_label = runtime_record.name if runtime_record else event.runtime_id
            lines.append(f'  {runtime}["{runtime_label}\\n{event.runtime_id}\\n{event.external_version or "unversioned"}"]')
            lines.append(f'  {adapter}["{event.adapter_id}"]')
            lines.append(f"  {runtime} --> {adapter}")
            lines.append(f"  {adapter} --> audit")
            record = adapters.get(event.adapter_id)
            if record and record.contract == "crawler.v0":
                lines.append("  contract_crawler_v0[\"crawler.v0\"] --> evidence[Evidence Ledger]")
                lines.append(f"  {adapter} --> contract_crawler_v0")
            elif record and record.contract == "agent.v0":
                lines.append("  contract_agent_v0[\"agent.v0\"] --> result[AgentResult]")
                lines.append(f"  {adapter} --> contract_agent_v0")
        return "\n".join(dict.fromkeys(lines)) + "\n"

    def candidate_state_graph(self) -> str:
        lines = ["stateDiagram-v2"]
        for source, targets in TRANSITIONS.items():
            for target in sorted(targets):
                lines.append(f"  {source} --> {target}")
        return "\n".join(lines) + "\n"

    def write(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "system-fact-architecture.mmd").write_text(self.fact_architecture(), encoding="utf-8")
        (output_dir / "component-lifecycle.mmd").write_text(self.lifecycle_graph(), encoding="utf-8")
        (output_dir / "runtime-topology.mmd").write_text(self.runtime_graph(), encoding="utf-8")
        (output_dir / "candidate-state.mmd").write_text(self.candidate_state_graph(), encoding="utf-8")



