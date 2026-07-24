"""Independent registry of entities authorized to interpret Evidence as Facts."""
from __future__ import annotations

from .contracts import FactProducer


class FactProducerRegistry:
    def __init__(self) -> None:
        self._producers: dict[tuple[str, str], FactProducer] = {}

    def register(self, producer: FactProducer) -> None:
        key = (producer.producer_id, producer.producer_version)
        if key in self._producers:
            raise ValueError("fact producer already registered")
        self._producers[key] = producer

    def get(self, producer_id: str, producer_version: str) -> FactProducer | None:
        return self._producers.get((producer_id, producer_version))