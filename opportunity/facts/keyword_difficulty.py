"""Deterministic measurement contract for ``keyword_difficulty@0.1``."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SearchResultObservation:
    position: int
    domain: str
    competition_score: float

    def __post_init__(self) -> None:
        if not isinstance(self.position, int) or self.position < 1:
            raise ValueError("search result position must be a positive integer")
        if not isinstance(self.domain, str) or not self.domain.strip():
            raise ValueError("search result domain is required")
        if (
            not isinstance(self.competition_score, (int, float))
            or isinstance(self.competition_score, bool)
            or not 0 <= self.competition_score <= 100
        ):
            raise ValueError("search result competition score must be 0..100")


@dataclass(frozen=True, slots=True)
class KeywordDifficultyMeasurement:
    source_reference: str
    query: str
    ranked_results: tuple[SearchResultObservation, ...]
    calculation_rule: str
    result: float

    calculation_rule_id = "mean_result_competition_score_v1"

    def __post_init__(self) -> None:
        if not isinstance(self.source_reference, str) or not self.source_reference:
            raise ValueError("keyword difficulty measurement requires source reference")
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("keyword difficulty measurement requires query")
        if len(self.ranked_results) < 3:
            raise ValueError("keyword difficulty measurement requires at least three ranked results")
        positions = tuple(item.position for item in self.ranked_results)
        if positions != tuple(range(1, len(positions) + 1)):
            raise ValueError("ranked results must be ordered from position one without gaps")
        if self.calculation_rule != self.calculation_rule_id:
            raise ValueError("keyword difficulty calculation rule is not supported")
        expected = round(
            sum(item.competition_score for item in self.ranked_results) / len(self.ranked_results),
            2,
        )
        if self.result != expected:
            raise ValueError("keyword difficulty result does not match ranked result observations")

    @classmethod
    def from_metadata(
        cls, raw_reference: str, metadata: Mapping[str, Any]
    ) -> "KeywordDifficultyMeasurement":
        value = metadata.get("keyword_difficulty_measurement")
        if not isinstance(value, Mapping):
            raise ValueError("keyword difficulty evidence is missing measurement")
        source_reference = value.get("source_reference")
        if source_reference != raw_reference:
            raise ValueError("keyword difficulty source reference must match evidence")
        query = value.get("query")
        results = value.get("ranked_results")
        calculation_rule = value.get("calculation_rule")
        if not isinstance(results, (tuple, list)):
            raise ValueError("keyword difficulty ranked results are required")
        observations = tuple(
            SearchResultObservation(
                item.get("position"), item.get("domain"), item.get("competition_score")
            )
            for item in results
            if isinstance(item, Mapping)
        )
        if len(observations) != len(results):
            raise ValueError("keyword difficulty ranked results must be structured records")
        score = round(
            sum(item.competition_score for item in observations) / len(observations), 2
        ) if observations else 0.0
        return cls(source_reference, query, observations, calculation_rule, score)

    def as_measurements(self) -> Mapping[str, object]:
        return MappingProxyType({
            "source_reference": self.source_reference,
            "query": self.query,
            "ranked_results": tuple({
                "position": item.position,
                "domain": item.domain,
                "competition_score": item.competition_score,
            } for item in self.ranked_results),
            "calculation_rule": self.calculation_rule,
            "calculated_score": self.result,
        })