"""Extract direct Roblox page observations into neutral measurement artifacts only."""
from __future__ import annotations

from candidates.evidence_validator import EvidenceLookup

from .contracts import FactProducer, FactProductionRequest, FactSupport, MeasurementArtifact


class RobloxObservationFactProducer:
    """A bounded parser for recorded Roblox evidence; it makes no opportunity claim."""

    producer_id = "roblox-observation-fact-producer"
    producer_version = "0.1"
    measurement_method = "recorded-roblox-observation-v1"
    supported_fact_ids = (
        "game_title_observed",
        "creator_observed",
        "place_id_observed",
        "description_observed",
        "visit_count_observed",
        "player_count_observed",
    )
    _field_names = {
        "game_title_observed": "title",
        "creator_observed": "creator",
        "place_id_observed": "place_id",
        "description_observed": "description",
        "visit_count_observed": "visits",
        "player_count_observed": "active_players",
    }

    def __init__(self, evidence: EvidenceLookup) -> None:
        self._evidence = evidence

    @classmethod
    def registration(cls) -> FactProducer:
        return FactProducer(
            cls.producer_id,
            cls.producer_version,
            tuple(FactSupport(fact_id, "0.1", (cls.measurement_method,)) for fact_id in cls.supported_fact_ids),
        )

    def measure(self, request: FactProductionRequest) -> MeasurementArtifact:
        if (
            request.producer_id != self.producer_id
            or request.producer_version != self.producer_version
            or request.fact_version != "0.1"
            or request.fact_id not in self._field_names
            or len(request.evidence_ids) != 1
        ):
            raise ValueError("Roblox observation request does not match producer capability")
        evidence = self._evidence.get(request.evidence_ids[0])
        if evidence is None:
            raise KeyError(f"evidence not found in ledger: {request.evidence_ids[0]}")
        field = self._field_names[request.fact_id]
        observations = self._parse(evidence.raw_reference)
        if field not in observations:
            raise ValueError(f"Roblox evidence does not contain observed field: {field}")
        return MeasurementArtifact(
            request.request_id,
            request.producer_id,
            request.producer_version,
            request.fact_id,
            request.fact_version,
            request.evidence_ids,
            self.measurement_method,
            {"observed_field": field, "observed_value": observations[field]},
            observations[field],
            {
                "source_evidence_id": evidence.id,
                "source": evidence.source,
                "source_locator": evidence.metadata.get("source_locator", ""),
                "source_captured_at": evidence.captured_time,
                "producer_id": self.producer_id,
                "producer_version": self.producer_version,
            },
            captured_at=evidence.captured_time,
        )

    @staticmethod
    def _parse(raw_reference: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for part in raw_reference.split(";"):
            key, separator, value = part.strip().partition("=")
            if separator and key and value.strip():
                values[key] = value.strip()
        return values
