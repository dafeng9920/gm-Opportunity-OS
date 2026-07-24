"""Deterministically evaluate one Candidate from quality-accepted Gate Facts only."""
from __future__ import annotations

from typing import Protocol

from core.schemas import CandidatePacket
from opportunity.fact_quality.contracts import AcceptedFact
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus
from opportunity.evaluation.fact_validator import GateFactValidator

from .contracts import (
    DEFAULT_GATE_POLICY,
    GateAssessmentRecord,
    GateAssessmentStatus,
    GatePolicy,
)


class AcceptedFactLookup(Protocol):
    def list_accepted_for_evidence_ids(
        self, evidence_ids: tuple[str, ...]
    ) -> tuple[AcceptedFact, ...]: ...


class MultiFactGateEvaluator:
    """Aggregates accepted facts; it does not interpret opportunity value."""

    def __init__(
        self,
        facts: AcceptedFactLookup,
        gates: OpportunityGateEngine | None = None,
        policy: GatePolicy = DEFAULT_GATE_POLICY,
    ) -> None:
        if not callable(getattr(facts, "list_accepted_for_evidence_ids", None)):
            raise TypeError("Multi-fact evaluation requires AcceptedFact lookup")
        self._facts = facts
        self._gates = gates or OpportunityGateEngine()
        self._policy = policy
        self._validator = GateFactValidator()

    def evaluate(self, candidate: CandidatePacket) -> GateAssessmentRecord:
        accepted = self._facts.list_accepted_for_evidence_ids(candidate.evidence_ids)
        if any(not isinstance(item, AcceptedFact) for item in accepted):
            raise TypeError("Multi-fact evaluation requires AcceptedFact")
        if any(not set(item.fact.evidence_ids).issubset(candidate.evidence_ids) for item in accepted):
            raise ValueError("accepted fact evidence is outside candidate evidence")

        by_fact: dict[str, AcceptedFact] = {}
        duplicates: set[str] = set()
        for item in accepted:
            if item.fact.fact_id not in self._policy.required_facts:
                continue
            self._validator.validate(item.fact)
            if item.fact.fact_id in by_fact:
                duplicates.add(item.fact.fact_id)
            else:
                by_fact[item.fact.fact_id] = item

        missing = tuple(
            fact_id for fact_id in self._policy.required_facts if fact_id not in by_fact
        )
        reasons = tuple(f"missing_fact:{fact_id}" for fact_id in missing) + tuple(
            f"duplicate_fact:{fact_id}" for fact_id in sorted(duplicates)
        )
        inputs = {fact_id: item.fact.value for fact_id, item in by_fact.items()}
        results = self._gates.assess(candidate, inputs).results
        if missing or duplicates:
            status = GateAssessmentStatus.UNKNOWN
        elif any(result.status is GateStatus.FAIL for result in results):
            status = GateAssessmentStatus.FAIL
            reasons += tuple(
                f"gate_failed:{result.gate}"
                for result in results
                if result.status is GateStatus.FAIL
            )
        elif any(result.status is not GateStatus.PASS for result in results):
            status = GateAssessmentStatus.UNKNOWN
            reasons += tuple(
                f"gate_unknown:{result.gate}"
                for result in results
                if result.status is not GateStatus.PASS
            )
        else:
            status = GateAssessmentStatus.PASS

        return GateAssessmentRecord(
            candidate.id,
            tuple(item.accepted_fact_id for item in by_fact.values()),
            results,
            status,
            reasons,
            self._policy.policy_id,
            self._policy.version,
        )