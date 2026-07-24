"""Read-only integrity checks for AnalysisProposal source references."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Protocol

from core.schemas import EvidenceObject

from .contracts import AnalysisProposal


class EvidenceLookup(Protocol):
    def get(self, evidence_id: str) -> EvidenceObject | None: ...


class MeasurementArtifactLookup(Protocol):
    def get_measurement(self, artifact_id: str): ...


class AnalysisProposalReferenceValidator:
    """Validates existing source IDs; it never produces Facts or executes analysis."""

    def __init__(self, measurements: MeasurementArtifactLookup, evidence: EvidenceLookup) -> None:
        self._measurements = measurements
        self._evidence = evidence

    def validate(self, proposal: AnalysisProposal) -> None:
        allowed_evidence: set[str] = set()
        for artifact_id in proposal.measurement_artifact_ids:
            artifact = self._measurements.get_measurement(artifact_id)
            if artifact is None:
                raise KeyError(f"measurement artifact not found: {artifact_id}")
            allowed_evidence.update(self._evidence_ids(artifact))
        for evidence_id in proposal.evidence_ids:
            if self._evidence.get(evidence_id) is None:
                raise KeyError(f"evidence not found: {evidence_id}")
            if evidence_id not in allowed_evidence:
                raise ValueError("proposal evidence is outside referenced measurement scope")

    @staticmethod
    def _evidence_ids(artifact) -> tuple[str, ...]:
        value = artifact.get("evidence_ids") if isinstance(artifact, Mapping) else (artifact["evidence_ids"] if callable(getattr(artifact, "keys", None)) else getattr(artifact, "evidence_ids", None))
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, (tuple, list)) or not value or not all(isinstance(item, str) and item.strip() for item in value):
            raise ValueError("measurement artifact evidence references are invalid")
        return tuple(value)

