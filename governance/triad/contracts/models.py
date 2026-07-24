"""Stable input/output contracts for the non-executing governance layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class GateDecision(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class Role(StrEnum):
    EXECUTION = "EXECUTION"
    REVIEW = "REVIEW"
    COMPLIANCE = "COMPLIANCE"


@dataclass(frozen=True)
class GovernanceTask:
    """A request to govern an existing artifact; never a request to execute work."""

    id: str
    objective: str
    input_refs: tuple[str, ...]
    expected_output: str
    scope: str = "admission"
    metadata: Mapping[str, str] = field(default_factory=dict)
    candidate_id: str = ""


@dataclass(frozen=True)
class RoleArtifact:
    task_id: str
    role: Role
    summary: str
    formal: bool = True
    input_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateDecisionRecord:
    task_id: str
    decision: GateDecision
    rationale: str
    issued_by: Role = Role.COMPLIANCE
