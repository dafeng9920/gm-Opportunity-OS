"""Contracts for governed production of Gate Facts from ledger evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4

from opportunity.evaluation.contracts import EvaluationFact


def now() -> str:
    return datetime.now(UTC).isoformat()


def freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class FactSupport:
    fact_id: str
    fact_version: str
    measurement_methods: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.fact_id or not self.fact_version or not self.measurement_methods or not all(self.measurement_methods):
            raise ValueError("fact support identity and measurement methods are required")


@dataclass(frozen=True, slots=True)
class FactProducer:
    producer_id: str
    producer_version: str
    supported_facts: tuple[FactSupport, ...]
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.producer_id or not self.producer_version or not self.supported_facts or not self.created_at:
            raise ValueError("fact producer identity and support are required")
        if len({(item.fact_id, item.fact_version) for item in self.supported_facts}) != len(self.supported_facts):
            raise ValueError("fact producer support must be unique")


@dataclass(frozen=True, slots=True)
class FactProductionRequest:
    producer_id: str
    producer_version: str
    fact_id: str
    fact_version: str
    evidence_ids: tuple[str, ...]
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all((self.producer_id, self.producer_version, self.fact_id, self.fact_version, self.request_id, self.created_at)):
            raise ValueError("fact production request identity is required")
        if not self.evidence_ids or not all(self.evidence_ids) or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("fact production request requires unique evidence ids")


@dataclass(frozen=True, slots=True)
class MeasurementArtifact:
    request_id: str
    producer_id: str
    producer_version: str
    fact_id: str
    fact_version: str
    evidence_ids: tuple[str, ...]
    measurement_method: str
    measurements: Mapping[str, Any]
    output_value: Any
    provenance: Mapping[str, Any]
    artifact_id: str = field(default_factory=lambda: str(uuid4()))
    captured_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all((self.request_id, self.producer_id, self.producer_version, self.fact_id, self.fact_version, self.measurement_method, self.artifact_id, self.captured_at)):
            raise ValueError("measurement artifact identity is required")
        if not self.evidence_ids or not all(self.evidence_ids) or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("measurement artifact requires unique evidence ids")
        if not isinstance(self.measurements, Mapping) or not isinstance(self.provenance, Mapping):
            raise ValueError("measurement artifact measurements and provenance must be mappings")
        object.__setattr__(self, "measurements", freeze(dict(self.measurements)))
        object.__setattr__(self, "provenance", freeze(dict(self.provenance)))
        object.__setattr__(self, "output_value", freeze(self.output_value))


@dataclass(frozen=True, slots=True)
class ProducedGateFact:
    production_id: str
    request_id: str
    producer_id: str
    producer_version: str
    measurement_artifact_id: str
    fact: EvaluationFact
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all((self.production_id, self.request_id, self.producer_id, self.producer_version, self.measurement_artifact_id, self.created_at)):
            raise ValueError("produced gate fact identity is required")