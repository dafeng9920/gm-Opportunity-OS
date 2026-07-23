from __future__ import annotations

from dataclasses import dataclass

from governance.triad.contracts import GovernanceTask


@dataclass(frozen=True)
class ChecklistResult:
    ready: bool
    issues: tuple[str, ...]


class DispatchChecklist:
    """Pre-dispatch gate derived from the source checklist, without GM-Lite workflow rules."""

    _FORBIDDEN_SCOPE_TERMS = (
        "produce_content", "discover_opportunities", "crawl", "build_site", "write_code",
        "modify_code", "business_direction",
    )

    def validate(self, task: GovernanceTask) -> ChecklistResult:
        issues: list[str] = []
        if not task.id.strip():
            issues.append("task id is required")
        if not task.objective.strip():
            issues.append("responsibility/objective is required")
        if not task.input_refs:
            issues.append("at least one immutable input reference is required")
        if not task.expected_output.strip():
            issues.append("an output contract is required")
        if task.scope.strip().lower() != "admission":
            issues.append("governance scope must be admission")
        scope_text = " ".join((task.scope, task.objective, task.expected_output)).lower()
        for term in self._FORBIDDEN_SCOPE_TERMS:
            if term in scope_text:
                issues.append(f"governance cannot request capability: {term}")
        return ChecklistResult(not issues, tuple(issues))
