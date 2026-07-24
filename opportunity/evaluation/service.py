"""Evaluate a persisted Candidate through governed Fact production outputs and the stable Gate Engine."""
from __future__ import annotations

from candidates.repository import CandidateRepository
from opportunity.gates import OpportunityGateEngine

from .contracts import CandidateEvaluationResult
from .gate_adapter import EvaluationGateAdapter
from .resolver import EvidenceResolver


class CandidateEvaluationService:
    def __init__(self, candidates: CandidateRepository, resolver: EvidenceResolver, gates: OpportunityGateEngine, supported_domains: tuple[str, ...], adapter: EvaluationGateAdapter | None = None) -> None:
        if not supported_domains or not all(isinstance(domain, str) and domain.strip() for domain in supported_domains):
            raise ValueError("supported evaluation domains are required")
        self._candidates = candidates
        self._resolver = resolver
        self._gates = gates
        self._supported_domains = frozenset(supported_domains)
        self._adapter = adapter or EvaluationGateAdapter()

    def evaluate(self, candidate_id: str, domain: str) -> CandidateEvaluationResult:
        if domain not in self._supported_domains:
            raise ValueError(f"unsupported evaluation domain: {domain}")
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise KeyError("candidate not found")
        context = self._resolver.resolve(candidate, domain)
        gate_input = self._adapter.to_gate_input(context)
        return CandidateEvaluationResult(candidate.id, context, gate_input, self._gates.assess(candidate, gate_input.as_mapping()))