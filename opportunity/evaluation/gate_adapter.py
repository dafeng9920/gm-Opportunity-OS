"""Adapt verified Evaluation Context facts to the unchanged generic Gate input mapping."""

from __future__ import annotations

from .contracts import (
    EvaluationContext,
    EvaluationFactCategory,
    FactVerification,
    GateInputField,
    GateInputMapping,
)


class EvaluationGateAdapter:
    """Only verified facts with matching category may become Gate inputs."""

    REQUIRED_FIELDS = {
        "trend_up": EvaluationFactCategory.DEMAND,
        "keyword_difficulty": EvaluationFactCategory.COMPETITION,
        "long_tail_count": EvaluationFactCategory.CONTENT,
        "available_sources": EvaluationFactCategory.DATA,
        "monetization_path": EvaluationFactCategory.MONETIZATION,
    }

    def to_gate_input(self, context: EvaluationContext) -> GateInputMapping:
        by_fact = {}
        for fact in context.facts:
            if fact.verification is not FactVerification.EVIDENCE_BACKED:
                continue
            if fact.fact_id in self.REQUIRED_FIELDS:
                if fact.fact_id in by_fact:
                    raise ValueError(f"duplicate verified evaluation fact: {fact.fact_id}")
                if fact.category is not self.REQUIRED_FIELDS[fact.fact_id]:
                    raise ValueError(f"evaluation fact category does not match gate field: {fact.fact_id}")
                by_fact[fact.fact_id] = fact
        missing = tuple(field for field in self.REQUIRED_FIELDS if field not in by_fact)
        if missing:
            raise ValueError("evaluation context is missing verified gate facts: " + ", ".join(missing))
        fields = tuple(
            GateInputField(field, by_fact[field].value, by_fact[field].fact_id, by_fact[field].evidence_ids)
            for field in self.REQUIRED_FIELDS
        )
        return GateInputMapping(context.candidate_id, fields)
