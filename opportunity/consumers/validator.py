"""Contract validator. It authorizes no read and makes no packet-store call."""
from __future__ import annotations
from .contracts import ConsumerAction, PacketReadRequest
from .registry import ConsumerRegistry
class ConsumerValidator:
    def __init__(self, registry: ConsumerRegistry) -> None: self._registry=registry
    def validate_read_request(self, request: PacketReadRequest, consumer_version: str) -> None:
        identity=self._registry.get_identity(request.consumer_id,consumer_version)
        capability=self._registry.get_capability(request.consumer_id,consumer_version)
        if identity is None or capability is None: raise KeyError('consumer is not registered')
        if request.requested_action not in capability.allowed_actions: raise PermissionError('consumer action is not allowed')
        if request.packet_reference.packet_version not in capability.allowed_packet_versions: raise PermissionError('packet version is not allowed')
        if request.contract_version != request.packet_reference.packet_version: raise ValueError('request contract version does not match packet version')
