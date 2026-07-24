"""Deterministic measurement contract for ``long_tail_count@0.1``."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _contains_contiguous(tokens: tuple[str, ...], scope: tuple[str, ...]) -> bool:
    return any(tokens[index:index + len(scope)] == scope for index in range(len(tokens) - len(scope) + 1))


@dataclass(frozen=True, slots=True)
class LongTailMeasurement:
    topic_scope: str
    source_reference: str
    candidate_items: tuple[str, ...]
    count_rule: str
    result: int

    count_rule_id = "qualified_long_tail_v1"

    def __post_init__(self) -> None:
        normalized_scope = _normalize(self.topic_scope)
        if not normalized_scope:
            raise ValueError("long tail measurement requires topic scope")
        if not isinstance(self.source_reference, str) or not self.source_reference:
            raise ValueError("long tail measurement requires source reference")
        if not self.candidate_items or not all(
            isinstance(item, str) and _normalize(item) for item in self.candidate_items
        ):
            raise ValueError("long tail measurement requires candidate items")
        if self.count_rule != self.count_rule_id:
            raise ValueError("long tail count rule is not supported")
        if not isinstance(self.result, int) or isinstance(self.result, bool) or self.result < 0:
            raise ValueError("long tail measurement result must be a non-negative integer")
        if self.result != len(self.qualified_items):
            raise ValueError("long tail measurement result does not match qualified candidate items")

    @property
    def normalized_scope(self) -> tuple[str, ...]:
        return tuple(_normalize(self.topic_scope).split())

    @property
    def normalized_candidate_items(self) -> tuple[str, ...]:
        return tuple(_normalize(item) for item in self.candidate_items)

    @property
    def qualified_items(self) -> tuple[str, ...]:
        scope = self.normalized_scope
        qualified: list[str] = []
        for item in self.normalized_candidate_items:
            tokens = tuple(item.split())
            if len(tokens) > len(scope) and _contains_contiguous(tokens, scope) and item not in qualified:
                qualified.append(item)
        return tuple(qualified)

    @classmethod
    def from_metadata(
        cls, raw_reference: str, metadata: Mapping[str, Any]
    ) -> "LongTailMeasurement":
        value = metadata.get("long_tail_measurement")
        if not isinstance(value, Mapping):
            raise ValueError("long tail evidence is missing measurement")
        source_reference = value.get("source_reference")
        if source_reference != raw_reference:
            raise ValueError("long tail source reference must match evidence")
        candidate_items = value.get("candidate_items")
        if not isinstance(candidate_items, (tuple, list)):
            raise ValueError("long tail candidate items are required")
        return cls(
            value.get("topic_scope"),
            source_reference,
            tuple(candidate_items),
            value.get("count_rule"),
            value.get("result"),
        )

    def as_measurements(self) -> Mapping[str, object]:
        return MappingProxyType({
            "topic_scope": _normalize(self.topic_scope),
            "source_reference": self.source_reference,
            "candidate_items": self.normalized_candidate_items,
            "qualified_items": self.qualified_items,
            "count_rule": self.count_rule,
            "calculated_count": self.result,
        })