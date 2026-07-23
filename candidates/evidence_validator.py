"""Validate that selected evidence exists in the Evidence Ledger and is traceable."""

from __future__ import annotations

from typing import Protocol

from core.schemas import EvidenceObject


class EvidenceLookup(Protocol):
    def get(self, evidence_id: str) -> EvidenceObject | None: ...


class EvidenceReferenceValidator:
    """Read-only validation of Evidence references; it never creates Candidate facts."""

    def __init__(self, ledger: EvidenceLookup) -> None:
        self._ledger = ledger

    def validate(self, evidence_ids: tuple[str, ...]) -> tuple[EvidenceObject, ...]:
        if not evidence_ids:
            raise ValueError("evidence ids are required")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence ids must be unique")
        evidence_items: list[EvidenceObject] = []
        for evidence_id in evidence_ids:
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise ValueError("evidence id is invalid")
            evidence = self._ledger.get(evidence_id)
            if evidence is None:
                raise KeyError(f"evidence not found in ledger: {evidence_id}")
            for field_name in ("source", "captured_time", "content_hash"):
                value = getattr(evidence, field_name, "")
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"ledger evidence is missing {field_name}")
            evidence_items.append(evidence)
        return tuple(evidence_items)
