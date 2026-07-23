"""Versioned generic rules. They acquire no external data."""
from __future__ import annotations
from .contracts import GateDefinition, RuleDefinition

class GateRegistry:
    def __init__(self, definitions: tuple[GateDefinition, ...]) -> None:
        self._definitions = {(item.id, item.version): item for item in definitions}
    def get(self, gate_id: str, version: str = "0.1") -> GateDefinition:
        try:
            return self._definitions[(gate_id, version)]
        except KeyError as error:
            raise KeyError(f"unknown gate version: {gate_id}@{version}") from error
    def list(self) -> tuple[GateDefinition, ...]:
        return tuple(self._definitions.values())

DEFAULT_GATE_REGISTRY = GateRegistry((
    GateDefinition("demand", "0.1", "implemented", (RuleDefinition("trend_up", "equals", True, "trend_up"),)),
    GateDefinition("competition", "0.1", "implemented", (RuleDefinition("keyword_difficulty_max", "max", 30, "keyword_difficulty"),)),
    GateDefinition("content_expansion", "0.1", "implemented", (RuleDefinition("minimum_long_tail", "min", 10, "long_tail_count"),)),
    GateDefinition("data_availability", "0.1", "implemented", (RuleDefinition("required_sources", "contains_all", ("official", "community"), "available_sources"),)),
    GateDefinition("monetization", "0.1", "implemented", (RuleDefinition("monetization_path", "present", True, "monetization_path"),)),
))
