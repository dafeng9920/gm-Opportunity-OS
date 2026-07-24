"""Produce deterministic long-tail-count measurements from persisted Evidence."""
from __future__ import annotations

from candidates.evidence_validator import EvidenceLookup

from .contracts import FactProducer, FactProductionRequest, FactSupport, MeasurementArtifact
from .long_tail import LongTailMeasurement


class LongTailCountProducer:
    """Produces ``long_tail_count@0.1`` measurement artifacts only."""

    producer_id = "long-tail-count-producer"
    producer_version = "0.1"
    fact_id = "long_tail_count"
    fact_version = "0.1"
    measurement_method = "qualified-long-tail-v1"

    def __init__(self, evidence: EvidenceLookup) -> None:
        self._evidence = evidence

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
            raise ValueError("long tail request does not match producer capability")
        if len(request.evidence_ids) != 1:
            raise ValueError("long tail producer requires exactly one keyword corpus evidence reference")
        evidence_id = request.evidence_ids[0]
        item = self._evidence.get(evidence_id)
        if item is None:
            raise KeyError(f"evidence not found in ledger: {evidence_id}")
        measurement = LongTailMeasurement.from_metadata(item.raw_reference, item.metadata)
        return MeasurementArtifact(
            request.request_id,
            request.producer_id,
            request.producer_version,
            request.fact_id,
            request.fact_version,
            request.evidence_ids,
            self.measurement_method,
            measurement.as_measurements(),
            measurement.result,
            {
                "query_family": measurement.topic_scope,
                "source": item.source,
                "source_reference": measurement.source_reference,
                "count_rule": measurement.count_rule,
            },
        )