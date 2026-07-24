"""Recorded public Roblox observations only; no network or evaluation behavior."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crawlers.contract import CrawlRequest, DiscoveryRecord


def _required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RecordedRobloxObservation:
    """One manually captured public observation, ready for the crawler boundary."""

    observation_id: str
    source: str
    source_type: str
    source_locator: str
    captured_at: str
    acquisition_method: str
    raw_payload_reference: str
    provenance: dict[str, Any]
    measurement_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "observation_id", "source", "source_type", "source_locator", "captured_at",
            "acquisition_method", "raw_payload_reference",
        ):
            _required(getattr(self, name), name)
        if not isinstance(self.provenance, dict) or not self.provenance:
            raise ValueError("provenance must be a non-empty object")
        if not isinstance(self.measurement_context, dict):
            raise ValueError("measurement_context must be an object")

    def as_discovery_record(self) -> DiscoveryRecord:
        return DiscoveryRecord(
            external_id=self.observation_id,
            source=self.source,
            source_type=self.source_type,
            raw_reference=self.raw_payload_reference,
            captured_time=self.captured_at,
            metadata={
                "source_locator": self.source_locator,
                "acquisition_method": self.acquisition_method,
                "raw_payload_reference": self.raw_payload_reference,
                "provenance": self.provenance,
                "measurement_context": self.measurement_context,
            },
        )


class RecordedRobloxGameAdapter:
    """Adapts supplied public captures into raw discoveries; it performs no fetches."""

    crawler_id = "adapter.roblox-recorded-game"

    def __init__(self, observations: tuple[RecordedRobloxObservation, ...]) -> None:
        if not observations:
            raise ValueError("at least one Roblox observation is required")
        self._observations = observations

    def crawl(self, request: CrawlRequest) -> tuple[DiscoveryRecord, ...]:
        if request.source != "roblox":
            raise ValueError("Roblox recorded adapter requires a roblox request source")
        return tuple(item.as_discovery_record() for item in self._observations)



