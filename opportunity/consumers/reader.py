"""Internal read-only service; it never writes or executes evaluation components."""
from __future__ import annotations
from opportunity.packets.store import OpportunityPacketStore
from .contracts import PacketReadRequest
from .query_validator import PacketQueryValidator
from .read_contracts import PacketQuery, PacketReadResult, PacketSnapshot
from .validator import ConsumerValidator
class OpportunityPacketReader:
    def __init__(self, consumers: ConsumerValidator, store: OpportunityPacketStore, queries: PacketQueryValidator | None = None) -> None:
        self._consumers=consumers; self._store=store; self._queries=queries or PacketQueryValidator()
    def read(self, request: PacketReadRequest, consumer_version: str, query: PacketQuery) -> PacketReadResult:
        self._consumers.validate_read_request(request,consumer_version); self._queries.validate(query)
        if query.opportunity_id and query.opportunity_id != request.packet_reference.packet_id: raise ValueError('query packet id must match read request')
        if query.version and query.version != request.packet_reference.packet_version: raise ValueError('query packet version must match read request')
        records=self._store.query(opportunity_id=request.packet_reference.packet_id,version=request.packet_reference.packet_version,domain=query.domain,lifecycle=query.lifecycle_status,limit=query.limit)
        snapshots=tuple(PacketSnapshot(item.opportunity_id,item.version,item.lifecycle,item.payload) for item in records)
        return PacketReadResult(request.request_id,snapshots,len(snapshots))
