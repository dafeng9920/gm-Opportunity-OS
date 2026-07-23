from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DECISIONS = frozenset({"ADOPT", "ADAPT", "REIMPLEMENT", "REJECT"})
Decision = Literal["ADOPT", "ADAPT", "REIMPLEMENT", "REJECT"]


@dataclass(frozen=True, slots=True)
class ComponentEvaluation:
    """A decision record; it does not register or activate a component."""
    component_name: str
    source: str
    version: str
    license: str
    install_method: str
    dependency_report: str
    capability_summary: str
    security_review: str
    contract_fit: str
    decision: Decision

    def __post_init__(self) -> None:
        for field_name in ("component_name", "source", "version", "license", "install_method", "dependency_report", "capability_summary", "security_review", "contract_fit"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.decision not in DECISIONS:
            raise ValueError("decision must be ADOPT, ADAPT, REIMPLEMENT, or REJECT")
