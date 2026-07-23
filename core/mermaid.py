from __future__ import annotations

from pathlib import Path

from core.registry import ComponentRegistry
from core.state import TRANSITIONS


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value)


def architecture(registry: ComponentRegistry) -> str:
    lines = ["flowchart LR", "  signal[External Signal] --> evidence[Evidence Object]", "  evidence --> candidate[Candidate Packet]", "  candidate --> handoff[Handoff Queue]"]
    for component in registry.list():
        node = _safe_id(component.id)
        lines.append(f'  {node}["{component.name}\\n({component.type}, {component.status})"]')
        lines.append(f"  registry[(Component Registry)] -. registers .-> {node}")
    return "\n".join(lines) + "\n"


def state_flow() -> str:
    lines = ["stateDiagram-v2"]
    for source, targets in TRANSITIONS.items():
        for target in sorted(targets):
            lines.append(f"  {source} --> {target}")
    return "\n".join(lines) + "\n"


def component_registry(registry: ComponentRegistry) -> str:
    lines = ["flowchart TB", "  registry[(Component Registry)]"]
    for component in registry.list():
        node = _safe_id(component.id)
        lines.append(f'  {node}["{component.name}: {component.capability}"]')
        lines.append(f"  registry --> {node}")
    return "\n".join(lines) + "\n"


def write_diagrams(registry: ComponentRegistry, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "fact-architecture.mmd").write_text(architecture(registry), encoding="utf-8")
    (output_dir / "state-flow.mmd").write_text(state_flow(), encoding="utf-8")
    (output_dir / "component-registry.mmd").write_text(component_registry(registry), encoding="utf-8")
