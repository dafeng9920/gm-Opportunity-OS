"""Rule and result contracts. None express a commercial conclusion."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

class GateStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"

@dataclass(frozen=True, slots=True)
class RuleDefinition:
    id: str
    operator: str
    expected: Any
    field: str

@dataclass(frozen=True, slots=True)
class GateDefinition:
    id: str
    version: str
    status: str
    rules: tuple[RuleDefinition, ...]
    def __post_init__(self) -> None:
        if not self.id or not self.version or self.status != "implemented" or not self.rules:
            raise ValueError("gate requires id, version, implemented status, and rules")

@dataclass(frozen=True, slots=True)
class RuleResult:
    rule_id: str
    status: GateStatus
    observed: Any
    expected: Any

@dataclass(frozen=True, slots=True)
class OpportunityGateResult:
    candidate_id: str
    gate: str
    version: str
    status: GateStatus
    evidence_refs: tuple[str, ...]
    rule_results: tuple[RuleResult, ...]
    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["rule_results"] = [{**asdict(rule), "status": rule.status.value} for rule in self.rule_results]
        return result

@dataclass(frozen=True, slots=True)
class OpportunityGateAssessment:
    candidate_id: str
    results: tuple[OpportunityGateResult, ...]
