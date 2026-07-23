from __future__ import annotations
import json
from dataclasses import asdict
from enum import Enum
from typing import Any
from .models import OpportunityPacket
def _value(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if isinstance(value, tuple): return [_value(item) for item in value]
    if isinstance(value, dict): return {key: _value(item) for key, item in value.items()}
    return value
class OpportunityPacketSerializer:
    def to_dict(self, packet: OpportunityPacket) -> dict[str, Any]: return _value(asdict(packet))
    def to_json(self, packet: OpportunityPacket) -> str: return json.dumps(self.to_dict(packet), sort_keys=True)
