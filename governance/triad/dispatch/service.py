from __future__ import annotations

from dataclasses import dataclass

from governance.triad.checklist import DispatchChecklist
from governance.triad.contracts import GovernanceTask, Role


@dataclass(frozen=True)
class TriadDispatch:
    task: GovernanceTask
    roles: tuple[Role, ...] = (Role.EXECUTION, Role.REVIEW, Role.COMPLIANCE)
    gate_outputs: tuple[str, ...] = ("ALLOW", "BLOCK", "REVIEW_REQUIRED")


class TriadDispatchService:
    """Produces a governed review plan. It contains no executor, tool, or Core mutation path."""

    def __init__(self, checklist: DispatchChecklist | None = None) -> None:
        self._checklist = checklist or DispatchChecklist()

    def create(self, task: GovernanceTask) -> TriadDispatch:
        result = self._checklist.validate(task)
        if not result.ready:
            raise ValueError("dispatch blocked: " + "; ".join(result.issues))
        return TriadDispatch(task=task)
