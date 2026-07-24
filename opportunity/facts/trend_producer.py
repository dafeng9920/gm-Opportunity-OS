"""Produce deterministic trend measurements from persisted Trend Evidence."""
from __future__ import annotations

from candidates.evidence_validator import EvidenceLookup

from .contracts import FactProducer, FactProductionRequest, FactSupport, MeasurementArtifact
from .trend import TrendMeasurement


class TrendSignalProducer:
    """Produces ``trend_up@0.1`` measurement artifacts; it makes no business decision."""

    producer_id = "trend-signal-producer"
    producer_version = "0.1"
    fact_id = "trend_up"
    fact_version = "0.1"
    measurement_method = "latest-greater-than-earliest-v1"

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
            raise ValueError("trend request does not match producer capability")
        if len(request.evidence_ids) != 1:
            raise ValueError("trend producer requires exactly one trend evidence reference")
        evidence_id = request.evidence_ids[0]
        item = self._evidence.get(evidence_id)
        if item is None:
            raise KeyError(f"evidence not found in ledger: {evidence_id}")
        measurement = TrendMeasurement.from_metadata(item.raw_reference, item.metadata)
        query = item.metadata.get("query")
        region = item.metadata.get("region")
        if not isinstance(query, str) or not query.strip() or not isinstance(region, str) or not region.strip():
            raise ValueError("trend evidence is missing query or region provenance")
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
                "query": query,
                "region": region,
                "time_window": measurement.time_window,
                "source": item.source,
                "source_reference": measurement.source_reference,
            },
        )