"""The only production boundary for Evidence-backed Candidate formation."""

from __future__ import annotations

from candidates.repository import CandidateRepository
from core.schemas import CandidatePacket

from .evidence_validator import EvidenceReferenceValidator
from .formation_contracts import CandidateFormationRequest, CandidateFormationResult, now


class CandidateFormationService:
    """Validates ledger references, persists one Candidate, and makes no decision calls."""

    def __init__(
        self,
        validator: EvidenceReferenceValidator,
        repository: CandidateRepository,
        supported_domains: tuple[str, ...],
    ) -> None:
        if not supported_domains or not all(isinstance(domain, str) and domain.strip() for domain in supported_domains):
            raise ValueError("supported candidate formation domains are required")
        self._validator = validator
        self._repository = repository
        self._supported_domains = frozenset(supported_domains)

    def form(self, request: CandidateFormationRequest) -> CandidateFormationResult:
        if request.domain not in self._supported_domains:
            raise ValueError(f"unsupported candidate formation domain: {request.domain}")
        evidence_items = self._validator.validate(request.evidence_ids)
        sources = {item.source for item in evidence_items}
        candidate = CandidatePacket(
            title=request.entity,
            signal="evidence-backed candidate",
            evidence_ids=request.evidence_ids,
            source=next(iter(sources)) if len(sources) == 1 else "evidence-ledger",
            confidence=request.confidence,
        )
        self._repository.create(candidate)
        return CandidateFormationResult(candidate.id, candidate, True, now())
