"""Crawler boundary contracts; no concrete external crawler integrations live here."""

from .contract import CrawlRequest, DiscoveryRecord, CrawlerPort
from .runner import CrawlerContractRunner

__all__ = ["CrawlRequest", "DiscoveryRecord", "CrawlerPort", "CrawlerContractRunner"]
