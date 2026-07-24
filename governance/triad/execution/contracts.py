"""Contracts for a future Triad execution runtime; this module executes nothing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import re
from uuid import uuid4

from governance.triad.contracts import Role


def now() -> str:
    return datetime.now(UTC).isoformat()


def validate_version(value: str, name: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+", value):
        raise ValueError(f"{name} version must be major.minor")


@dataclass(frozen=True, slots=True)
class TriadExecutionContext:
    execution_id: str
    governance_task_id: str
    candidate_id: str
    assessment_id: str
    version: str
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all(isinstance(item, str) and item.strip() for item in (
            self.execution_id, self.governance_task_id, self.candidate_id, self.assessment_id, self.created_at,
        )):
            raise ValueError("triad execution context identity is required")
        validate_version(self.version, "triad execution context")


@dataclass(frozen=True, slots=True)
class RoleInvocation:
    execution_id: str
    governance_task_id: str
    candidate_id: str
    assessment_id: str
    role: Role
    input_refs: tuple[str, ...]
    contract_version: str
    invocation_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all(isinstance(item, str) and item.strip() for item in (
            self.execution_id, self.governance_task_id, self.candidate_id, self.assessment_id,
            self.invocation_id, self.created_at,
        )):
            raise ValueError("role invocation identity is required")
        if not isinstance(self.role, Role):
            raise ValueError("role invocation role is invalid")
        if not isinstance(self.input_refs, tuple) or not self.input_refs or not all(isinstance(ref, str) and ref.strip() for ref in self.input_refs):
            raise ValueError("role invocation requires immutable input references")
        if len(set(self.input_refs)) != len(self.input_refs):
            raise ValueError("role invocation input references must be unique")
        validate_version(self.contract_version, "role invocation")


class RoleResultStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class RoleResult:
    execution_id: str
    governance_task_id: str
    role: Role
    status: RoleResultStatus
    summary: str
    artifact_refs: tuple[str, ...]
    audit_refs: tuple[str, ...]
    contract_version: str
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all(isinstance(item, str) and item.strip() for item in (
            self.execution_id, self.governance_task_id, self.summary, self.contract_version, self.created_at,
        )):
            raise ValueError("role result identity is required")
        if not isinstance(self.role, Role) or not isinstance(self.status, RoleResultStatus):
            raise ValueError("role result role or status is invalid")
        for refs, name in ((self.artifact_refs, "artifact"), (self.audit_refs, "audit")):
            if not isinstance(refs, tuple) or not all(isinstance(ref, str) and ref.strip() for ref in refs):
                raise ValueError(f"role result {name} references must be immutable strings")
            if len(set(refs)) != len(refs):
                raise ValueError(f"role result {name} references must be unique")
        validate_version(self.contract_version, "role result")