"""Deterministic measurement contract for ``trend_up@0.1``."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TrendMeasurement:
    """A reproducible two-point trend comparison bound to one Evidence record."""

    source_reference: str
    time_window: tuple[str, str]
    observations: tuple[float, ...]
    comparison_rule: str
    result: bool

    comparison_rule_id = "latest_gt_earliest"

    def __post_init__(self) -> None:
        if not isinstance(self.source_reference, str) or not self.source_reference or len(self.time_window) != 2 or not all(isinstance(value, str) and value for value in self.time_window):
            raise ValueError("trend measurement requires source reference and time window")
        if len(self.observations) < 2 or any(
            not isinstance(value, (int, float)) or isinstance(value, bool)
            for value in self.observations
        ):
            raise ValueError("trend measurement requires at least two numeric observations")
        if self.comparison_rule != self.comparison_rule_id:
            raise ValueError("trend measurement comparison rule is not supported")
        if self.result is not (self.observations[-1] > self.observations[0]):
            raise ValueError("trend measurement result does not match observations")

    @classmethod
    def from_metadata(cls, raw_reference: str, metadata: Mapping[str, Any]) -> "TrendMeasurement":
        value = metadata.get("trend_measurement")
        if not isinstance(value, Mapping):
            raise ValueError("trend evidence is missing trend measurement")
        source_reference = value.get("source_reference")
        if source_reference != raw_reference:
            raise ValueError("trend measurement source reference must match evidence")
        window = value.get("time_window")
        observations = value.get("observations")
        rule = value.get("comparison_rule")
        if not isinstance(window, (tuple, list)) or not isinstance(observations, (tuple, list)):
            raise ValueError("trend measurement time window and observations are required")
        observation_values = tuple(observations)
        if len(observation_values) < 2 or any(
            not isinstance(item, (int, float)) or isinstance(item, bool)
            for item in observation_values
        ):
            raise ValueError('trend measurement requires at least two numeric observations')
        return cls(
            source_reference,
            tuple(window),
            observation_values,
            rule,
            observation_values[-1] > observation_values[0] if len(observation_values) >= 2 else False,
        )

    def as_measurements(self) -> Mapping[str, object]:
        return MappingProxyType({
            "source_reference": self.source_reference,
            "time_window": self.time_window,
            "observations": self.observations,
            "comparison_rule": self.comparison_rule,
            "calculated_direction": self.result,
        })