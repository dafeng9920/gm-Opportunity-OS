"""Declared source catalogue and collector capabilities; entries are not collection permissions by themselves."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
class SourceStatus(StrEnum):
    REFERENCE_ONLY = "REFERENCE_ONLY"
    RESERVED = "RESERVED"
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
@dataclass(frozen=True)
class SourceCapability:
    id: str
    adapter_id: str
    supports: tuple[str, ...]
    limitations: tuple[str, ...]
@dataclass(frozen=True)
class SourceDefinition:
    id: str
    name: str
    source_type: str
    status: SourceStatus
    notes: str
    capabilities: tuple[SourceCapability, ...] = ()
class SourceRegistry:
    def __init__(self, sources: tuple[SourceDefinition, ...] | None = None) -> None: self._sources = sources or DEFAULT_SOURCES
    def list(self) -> tuple[SourceDefinition, ...]: return self._sources
    def get(self, source_id: str) -> SourceDefinition | None: return next((item for item in self._sources if item.id == source_id), None)
DEFAULT_SOURCES = (
    SourceDefinition("steamdb", "SteamDB", "Reference", SourceStatus.REFERENCE_ONLY, "Reference catalogue only; no collector approved."),
    SourceDefinition("igdb", "IGDB", "API", SourceStatus.RESERVED, "Reserved pending API and policy evaluation."),
    SourceDefinition("youtube", "YouTube", "Signal", SourceStatus.ACTIVE, "Public channel RSS collector is active under restricted-v0.", (SourceCapability("youtube-rss", "adapter.youtube-signal", ("video_signal",), ("fixed channels", "no search", "public RSS only")),)),
    SourceDefinition("roblox-official", "Roblox Official", "Data Source", SourceStatus.PLANNED, "Future plugin source; out of scope for v0.1."),
)
