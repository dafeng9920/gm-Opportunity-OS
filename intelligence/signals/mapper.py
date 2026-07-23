from crawlers.contract import DiscoveryRecord

from .contracts import SignalRecord, as_discovery_record


class SignalEvidenceMapper:
    """One-way mapping: signal observation -> DiscoveryRecord -> existing Evidence boundary."""

    def map(self, signal: SignalRecord) -> DiscoveryRecord:
        return as_discovery_record(signal)
