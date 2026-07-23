"""Deterministic router: produces plans from registered source capabilities and executes nothing."""
from __future__ import annotations
from intelligence.sources import SourceRegistry, SourceStatus
from .contracts import CollectorExecutionPlan, SignalQuery
class SignalRouter:
    def __init__(self, sources: SourceRegistry | None = None) -> None: self._sources = sources or SourceRegistry()
    def route(self, query: SignalQuery) -> tuple[CollectorExecutionPlan, ...]:
        plans = []
        selected = set(query.sources)
        for source in self._sources.list():
            if selected and source.id not in selected: continue
            if source.status is not SourceStatus.ACTIVE: continue
            for capability in source.capabilities:
                supported = tuple(item for item in query.signal_types if item in capability.supports)
                if supported:
                    plans.append(CollectorExecutionPlan(query.query_id, source.id, capability.adapter_id, supported, capability.limitations, query))
        return tuple(plans)
