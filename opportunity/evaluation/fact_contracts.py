"""Versioned, deterministic contracts for Gate Facts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .contracts import EvaluationFactCategory


class EvidenceSemantics(StrEnum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"


class FactValueType(StrEnum):
    BOOLEAN = "BOOLEAN"
    NUMBER = "NUMBER"
    INTEGER = "INTEGER"
    SOURCE_SET = "SOURCE_SET"
    NON_EMPTY_STRING = "NON_EMPTY_STRING"


@dataclass(frozen=True, slots=True)
class GateFactDefinition:
    fact_id: str
    version: str
    category: EvaluationFactCategory
    value_type: FactValueType
    evidence_semantics: EvidenceSemantics
    required_provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.fact_id or not self.version or not self.required_provenance:
            raise ValueError("gate fact definition identity and provenance are required")


class GateFactRegistry:
    def __init__(self, definitions: tuple[GateFactDefinition, ...]) -> None:
        self._definitions = {(item.fact_id, item.version): item for item in definitions}

    def get(self, fact_id: str, version: str) -> GateFactDefinition:
        try:
            return self._definitions[(fact_id, version)]
        except KeyError as error:
            raise ValueError(f"unknown gate fact version: {fact_id}@{version}") from error

    def list(self) -> tuple[GateFactDefinition, ...]:
        return tuple(self._definitions.values())


DEFAULT_GATE_FACT_REGISTRY = GateFactRegistry((
    GateFactDefinition("trend_up", "0.1", EvaluationFactCategory.DEMAND, FactValueType.BOOLEAN, EvidenceSemantics.SINGLE, ("query", "region", "time_window", "source", "method", "captured_at")),
    GateFactDefinition("keyword_difficulty", "0.1", EvaluationFactCategory.COMPETITION, FactValueType.NUMBER, EvidenceSemantics.SINGLE, ("query", "source", "method", "captured_at")),
    GateFactDefinition("long_tail_count", "0.1", EvaluationFactCategory.CONTENT, FactValueType.INTEGER, EvidenceSemantics.SINGLE, ("query_family", "source", "method", "captured_at")),
    GateFactDefinition("available_sources", "0.1", EvaluationFactCategory.DATA, FactValueType.SOURCE_SET, EvidenceSemantics.MULTI, ("source_inventory", "method", "captured_at")),
    GateFactDefinition("monetization_path", "0.1", EvaluationFactCategory.MONETIZATION, FactValueType.NON_EMPTY_STRING, EvidenceSemantics.SINGLE, ("path_scope", "source", "method", "captured_at")),
))


def value_matches(value: Any, value_type: FactValueType) -> bool:
    if value_type is FactValueType.BOOLEAN:
        return isinstance(value, bool)
    if value_type is FactValueType.NUMBER:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if value_type is FactValueType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if value_type is FactValueType.SOURCE_SET:
        return isinstance(value, (tuple, list, set, frozenset)) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)
    if value_type is FactValueType.NON_EMPTY_STRING:
        return isinstance(value, str) and bool(value.strip())
    return False
