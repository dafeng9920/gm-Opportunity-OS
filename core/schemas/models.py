from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

ComponentType = Literal["agent", "skill", "crawler", "adapter", "runtime", "plugin", "domain-plugin", "data_source"]
ComponentStatus = Literal["active", "inactive", "implemented", "deprecated"]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _required(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class Component:
    id: str
    name: str
    type: ComponentType
    version: str
    status: ComponentStatus
    capability: str
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in ("id", "name", "version", "capability", "created_at"):
            _required(getattr(self, field_name), field_name)
        if self.type not in {"agent", "skill", "crawler", "adapter", "runtime", "plugin", "domain-plugin", "data_source"}:
            raise ValueError("type is not a supported component type")
        if self.status not in {"active", "inactive", "implemented", "deprecated"}:
            raise ValueError("status is not a supported component status")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EvidenceObject:
    source: str
    source_type: str
    raw_reference: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    captured_time: str = field(default_factory=utc_now)
    content_hash: str = ""

    def __post_init__(self) -> None:
        for field_name in ("id", "source", "source_type", "raw_reference", "captured_time"):
            _required(getattr(self, field_name), field_name)
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")
        expected = sha256(self.raw_reference.encode("utf-8")).hexdigest()
        if self.content_hash and self.content_hash != expected:
            raise ValueError("content_hash does not match raw_reference")
        object.__setattr__(self, "content_hash", expected)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CandidatePacket:
    title: str
    signal: str
    evidence_ids: tuple[str, ...]
    source: str
    confidence: float
    status: str = "CANDIDATE_CREATED"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in ("id", "title", "signal", "source", "status", "created_at"):
            _required(getattr(self, field_name), field_name)
        if not self.evidence_ids or not all(isinstance(item, str) and item for item in self.evidence_ids):
            raise ValueError("evidence_ids must contain at least one ID")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        if not isinstance(self.confidence, (int, float)) or not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


@dataclass(frozen=True, slots=True)
class HandoffItem:
    candidate_id: str
    producer: str
    consumer: str
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    status: str = "pending"

    def __post_init__(self) -> None:
        for field_name in ("id", "candidate_id", "producer", "consumer", "created_at"):
            _required(getattr(self, field_name), field_name)
        if self.status not in {"pending", "claimed", "completed"}:
            raise ValueError("status is not supported")


@dataclass(frozen=True, slots=True)
class AdapterRegistration:
    """Registry metadata for a controlled adapter, distinct from its external backend."""
    adapter_id: str
    backend_component: str
    version: str
    permission_profile: str
    contract: str
    status: ComponentStatus
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in ("adapter_id", "backend_component", "version", "permission_profile", "contract", "created_at"):
            _required(getattr(self, field_name), field_name)
        if self.status not in {"active", "inactive", "deprecated"}:
            raise ValueError("status is not a supported adapter status")


@dataclass(frozen=True, slots=True)
class RuntimeRegistration:
    """Registry metadata for an isolated execution runtime, never an external tool itself."""
    runtime_id: str
    name: str
    runtime_type: str
    version: str
    policy: str
    status: str
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in ("runtime_id", "name", "runtime_type", "version", "policy", "status", "created_at"):
            _required(getattr(self, field_name), field_name)
        if self.status not in {"available", "unavailable", "deprecated"}:
            raise ValueError("status is not a supported runtime status")



