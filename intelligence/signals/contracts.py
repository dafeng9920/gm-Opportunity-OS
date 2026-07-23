"""Signal contracts: observations only, explicitly not opportunity decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from crawlers.contract import DiscoveryRecord


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class SignalRecord:
    source: str
    entity: str
    signal_type: str
    evidence: str
    confidence: float
    timestamp: str = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        for name in ("id", "source", "entity", "signal_type", "evidence", "timestamp"):
            _required(getattr(self, name), name)
        if not isinstance(self.confidence, (int, float)) or not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")


@dataclass(frozen=True, slots=True)
class YouTubeSignalRequest:
    query: str
    channel: str | None
    time_window: str

    def __post_init__(self) -> None:
        _required(self.query, "query")
        _required(self.time_window, "time_window")
        if self.channel is not None:
            _required(self.channel, "channel")


@dataclass(frozen=True, slots=True)
class VideoSignal(SignalRecord):
    video_id: str = ""

    def __post_init__(self) -> None:
        super(VideoSignal, self).__post_init__()
        _required(self.video_id, "video_id")
        if self.source != "youtube" or self.signal_type != "video":
            raise ValueError("VideoSignal requires source=youtube and signal_type=video")


class YouTubeSignalCollector(Protocol):
    """Future adapter boundary. This interface carries no implementation or network access."""

    collector_id: str

    def collect_signals(self, request: YouTubeSignalRequest) -> tuple[VideoSignal, ...]: ...


def as_discovery_record(signal: SignalRecord) -> DiscoveryRecord:
    """Maps an observation to the established acquisition contract; it does not persist it."""
    return DiscoveryRecord(
        external_id=signal.id,
        source=signal.source,
        source_type="signal",
        raw_reference=signal.evidence,
        captured_time=signal.timestamp,
        metadata={
            **signal.metadata,
            "entity": signal.entity,
            "signal_type": signal.signal_type,
            "signal_confidence": signal.confidence,
            "signal_id": signal.id,
        },
    )
