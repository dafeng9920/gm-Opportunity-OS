"""Validation boundary for facts that may become Evidence-backed Gate inputs."""

from __future__ import annotations

from .contracts import EvaluationFact, FactVerification
from .fact_contracts import DEFAULT_GATE_FACT_REGISTRY, EvidenceSemantics, GateFactRegistry, value_matches


class GateFactValidator:
    """Checks definition, provenance, value shape, and evidence cardinality."""

    def __init__(self, registry: GateFactRegistry = DEFAULT_GATE_FACT_REGISTRY) -> None:
        self._registry = registry

    def validate(self, fact: EvaluationFact) -> None:
        definition = self._registry.get(fact.fact_id, fact.fact_version)
        if fact.verification is not FactVerification.EVIDENCE_BACKED:
            raise ValueError("gate fact must be evidence-backed")
        if fact.category is not definition.category:
            raise ValueError("gate fact category does not match definition")
        if not value_matches(fact.value, definition.value_type):
            raise ValueError("gate fact value does not match definition")
        if definition.evidence_semantics is EvidenceSemantics.SINGLE and len(fact.evidence_ids) != 1:
            raise ValueError("gate fact requires exactly one evidence reference")
        if definition.evidence_semantics is EvidenceSemantics.MULTI and len(fact.evidence_ids) < 2:
            raise ValueError("gate fact requires multiple evidence references")
        missing = tuple(key for key in definition.required_provenance if not _present(fact.provenance.get(key)))
        if missing:
            raise ValueError("gate fact provenance is missing: " + ", ".join(missing))


def _present(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None