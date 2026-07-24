"""Deterministically measure classified source availability from persisted Evidence."""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from candidates.evidence_validator import EvidenceLookup

from .contracts import FactProducer, FactProductionRequest, FactSupport, MeasurementArtifact


class SourceInventoryProducer:
    """Produces the measurement artifact for ``available_sources@0.1`` only."""

    producer_id = "source-inventory-producer"
    producer_version = "0.1"
    fact_id = "available_sources"
    fact_version = "0.1"
    measurement_method = "evidence-source-type-v1"

    def __init__(
        self,
        evidence: EvidenceLookup,
        source_type_classifications: Mapping[str, str] | None = None,
    ) -> None:
        classifications = source_type_classifications or {
            "official-game-entity": "official",
            "community-update-log": "community",
        }
        if not classifications or not all(
            isinstance(source_type, str)
            and source_type.strip()
            and classification in {"official", "community"}
            for source_type, classification in classifications.items()
        ):
            raise ValueError("source inventory classifications must be explicit")
        self._evidence = evidence
        self._classifications = MappingProxyType(dict(classifications))

    @classmethod
    def registration(cls) -> FactProducer:
        return FactProducer(
            cls.producer_id,
            cls.producer_version,
            (FactSupport(cls.fact_id, cls.fact_version, (cls.measurement_method,)),),
        )

    def measure(self, request: FactProductionRequest) -> MeasurementArtifact:
        if (
            request.producer_id,
            request.producer_version,
            request.fact_id,
            request.fact_version,
        ) != (
            self.producer_id,
            self.producer_version,
            self.fact_id,
            self.fact_version,
        ):
            raise ValueError("source inventory request does not match producer capability")

        records: list[dict[str, str]] = []
        classifications: list[str] = []
        for evidence_id in request.evidence_ids:
            item = self._evidence.get(evidence_id)
            if item is None:
                raise KeyError(f"evidence not found in ledger: {evidence_id}")
            classification = self._classifications.get(item.source_type)
            if classification is None:
                raise ValueError(
                    f"source inventory has no classification for evidence type: {item.source_type}"
                )
            records.append(
                {
                    "evidence_id": item.id,
                    "source": item.source,
                    "source_type": item.source_type,
                    "raw_reference": item.raw_reference,
                    "classification": classification,
                }
            )
            if classification not in classifications:
                classifications.append(classification)

        return MeasurementArtifact(
            request.request_id,
            request.producer_id,
            request.producer_version,
            request.fact_id,
            request.fact_version,
            request.evidence_ids,
            self.measurement_method,
            {"source_records": tuple(records)},
            tuple(classifications),
            {"source_inventory": tuple(records)},
        )