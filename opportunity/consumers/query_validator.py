from __future__ import annotations
import re
from opportunity.packets.models import PacketLifecycle
from .read_contracts import PacketQuery
class PacketQueryValidator:
    MAX_LIMIT = 100
    def validate(self, query: PacketQuery) -> None:
        if not isinstance(query.limit, int) or not 1 <= query.limit <= self.MAX_LIMIT: raise ValueError('query limit must be between 1 and 100')
        if query.lifecycle_status is not None and not isinstance(query.lifecycle_status, PacketLifecycle): raise ValueError('query lifecycle status is invalid')
        if query.domain and not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', query.domain): raise ValueError('query domain format is invalid')
        if query.version and not re.fullmatch(r'\d+\.\d+', query.version): raise ValueError('query packet version format is invalid')
        if query.contract_version != '0.1': raise ValueError('query contract version is unsupported')
