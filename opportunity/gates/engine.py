"""Pure deterministic evaluation. No Core writer, Runtime, Agent, or Governance dependency."""
from __future__ import annotations
from typing import Any, Mapping
from core.schemas import CandidatePacket
from .contracts import GateStatus, OpportunityGateAssessment, OpportunityGateResult, RuleDefinition, RuleResult
from .rules import DEFAULT_GATE_REGISTRY, GateRegistry

class OpportunityGateEngine:
    def __init__(self, registry: GateRegistry = DEFAULT_GATE_REGISTRY) -> None:
        self._registry = registry
    def assess(self, candidate: CandidatePacket, inputs: Mapping[str, Any], blocked_gates: frozenset[str] = frozenset()) -> OpportunityGateAssessment:
        results = tuple(self.evaluate(candidate, definition.id, inputs, blocked_gates) for definition in self._registry.list())
        return OpportunityGateAssessment(candidate.id, results)
    def evaluate(self, candidate: CandidatePacket, gate_id: str, inputs: Mapping[str, Any], blocked_gates: frozenset[str] = frozenset(), version: str = "0.1") -> OpportunityGateResult:
        definition = self._registry.get(gate_id, version)
        if gate_id in blocked_gates:
            result = RuleResult("gate_block", GateStatus.BLOCKED, "blocked", "unblocked")
            return OpportunityGateResult(candidate.id, gate_id, version, GateStatus.BLOCKED, candidate.evidence_ids, (result,))
        rule_results = tuple(self._evaluate_rule(rule, inputs) for rule in definition.rules)
        statuses = {item.status for item in rule_results}
        status = GateStatus.FAIL if GateStatus.FAIL in statuses else GateStatus.UNKNOWN if GateStatus.UNKNOWN in statuses else GateStatus.PASS
        return OpportunityGateResult(candidate.id, gate_id, version, status, candidate.evidence_ids, rule_results)
    @staticmethod
    def _evaluate_rule(rule: RuleDefinition, inputs: Mapping[str, Any]) -> RuleResult:
        if rule.field not in inputs:
            return RuleResult(rule.id, GateStatus.UNKNOWN, None, rule.expected)
        value = inputs[rule.field]
        try:
            if rule.operator == "equals": passed = value == rule.expected
            elif rule.operator == "max": passed = value <= rule.expected
            elif rule.operator == "min": passed = value >= rule.expected
            elif rule.operator == "contains_all": passed = set(rule.expected).issubset(set(value))
            elif rule.operator == "present": passed = bool(value) is bool(rule.expected)
            else: raise ValueError(f"unsupported deterministic operator: {rule.operator}")
        except (TypeError, ValueError):
            return RuleResult(rule.id, GateStatus.UNKNOWN, value, rule.expected)
        return RuleResult(rule.id, GateStatus.PASS if passed else GateStatus.FAIL, value, rule.expected)
