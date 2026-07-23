"""Controlled YouTube RSS acquisition adapter. Public channel feeds only; no search, login, or browser automation."""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree
from crawlers.contract import CrawlRequest, DiscoveryRecord
from intelligence.signals.contracts import VideoSignal, as_discovery_record
from intelligence.query.contracts import CollectorExecutionPlan
ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/schemas/2015}"
class YoutubeFetchBackend(Protocol):
    def fetch(self, target: str, parameters: dict[str, Any]) -> str: ...
class YouTubeRssSignalAdapter:
    crawler_id = "adapter.youtube-signal"
    def __init__(self, backend: YoutubeFetchBackend) -> None: self._backend = backend
    def request_from_plan(self, plan: CollectorExecutionPlan) -> CrawlRequest:
        if plan.adapter_id != self.crawler_id: raise ValueError("execution plan is not for the YouTube RSS adapter")
        channel_id = str(plan.query.filters.get("channel_id", ""))
        if not channel_id: raise ValueError("YouTube RSS execution requires a fixed channel_id filter")
        return CrawlRequest("youtube", f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}", {"query": plan.query.filters.get("query", ""), "time_window": plan.query.time_window})
    def crawl(self, request: CrawlRequest) -> list[DiscoveryRecord]: return [as_discovery_record(item) for item in self.collect_signals(request)]
    def collect_signals(self, request: CrawlRequest) -> list[VideoSignal]:
        parsed = urlparse(request.target)
        if parsed.scheme != "https" or parsed.hostname != "www.youtube.com" or parsed.path != "/feeds/videos.xml": raise ValueError("YouTube adapter only permits the public RSS feed endpoint")
        channel_id = parse_qs(parsed.query).get("channel_id", [""])[0]
        if not channel_id: raise ValueError("YouTube RSS request requires channel_id")
        return self._parse(self._backend.fetch(request.target, dict(request.parameters)), channel_id, request.parameters)
    @staticmethod
    def _parse_window(value: Any) -> tuple[datetime | None, datetime | None]:
        if not value: return None, None
        try:
            start_text, end_text = str(value).split("/", 1); return datetime.fromisoformat(start_text).replace(tzinfo=UTC), datetime.fromisoformat(end_text).replace(tzinfo=UTC)
        except ValueError as error: raise ValueError("time_window must be YYYY-MM-DD/YYYY-MM-DD") from error
    def _parse(self, body: str, channel_id: str, parameters: dict[str, Any]) -> list[VideoSignal]:
        try: root = ElementTree.fromstring(body)
        except ElementTree.ParseError as error: raise ValueError("YouTube RSS response is not valid Atom XML") from error
        query = str(parameters.get("query", "")).strip().lower(); start, end = self._parse_window(parameters.get("time_window")); signals = []
        for entry in root.findall(f"{ATOM}entry"):
            title = entry.findtext(f"{ATOM}title", default="").strip(); video_id = entry.findtext(f"{YT}videoId", default="").strip(); published = entry.findtext(f"{ATOM}published", default="").strip()
            if not title or not video_id or not published: continue
            published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if query and query not in title.lower(): continue
            if (start and published_at < start) or (end and published_at > end.replace(hour=23, minute=59, second=59)): continue
            signals.append(VideoSignal(source="youtube", entity=title, signal_type="video", evidence=f"https://www.youtube.com/watch?v={video_id}", confidence=0.5, timestamp=published_at.isoformat(), metadata={"adapter_id": self.crawler_id, "channel_id": channel_id, "query": query, "published": published, "video_id": video_id}, video_id=video_id))
        return signals

