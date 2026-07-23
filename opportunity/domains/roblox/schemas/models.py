"""Roblox-only data schema. It defines supplied facts and performs no collection."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from opportunity.gates.contracts import OpportunityGateResult

@dataclass(frozen=True, slots=True)
class RobloxOpportunityCandidate:
    candidate_id: str
    game_name: str
    experience_id: str
    release_date: str | None
    search_keywords: tuple[str, ...]
    trend_signals: dict[str, Any]
    youtube_signals: dict[str, Any]
    serp_snapshot: tuple[str, ...]
    keyword_metrics: dict[str, Any]
    content_opportunities: tuple[str, ...]
    available_sources: tuple[str, ...]
    monetization_options: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    def __post_init__(self) -> None:
        for name in ("candidate_id", "game_name", "experience_id"):
            if not getattr(self, name): raise ValueError(f"{name} is required")
        if not self.evidence_refs or not all(self.evidence_refs):
            raise ValueError("evidence_refs are required")
        if not isinstance(self.trend_signals, dict) or not isinstance(self.keyword_metrics, dict):
            raise ValueError("signal and keyword metric fields must be objects")

@dataclass(frozen=True, slots=True)
class RobloxOpportunityAssessment:
    domain: str
    candidate_id: str
    gates: tuple[OpportunityGateResult, ...]
    evidence_refs: tuple[str, ...]
    unknowns: tuple[str, ...]
    risk_flags: tuple[str, ...]
    def __post_init__(self) -> None:
        if self.domain != "roblox": raise ValueError("assessment domain must be roblox")
