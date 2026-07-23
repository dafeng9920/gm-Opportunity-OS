import unittest

from intelligence.signals import SignalEvidenceMapper, VideoSignal, YouTubeSignalRequest
from intelligence.sources import SourceRegistry, SourceStatus


class IntelligenceSignalLayerTests(unittest.TestCase):
    def test_source_registry_declares_only_non_active_sources(self):
        registry = SourceRegistry()
        sources = {item.id: item for item in registry.list()}
        self.assertEqual(sources["steamdb"].status, SourceStatus.REFERENCE_ONLY)
        self.assertEqual(sources["igdb"].status, SourceStatus.RESERVED)
        self.assertEqual(sources["youtube"].status, SourceStatus.ACTIVE)
        self.assertEqual(sources["roblox-official"].status, SourceStatus.PLANNED)
        self.assertEqual({item.id for item in sources.values() if item.status is SourceStatus.ACTIVE}, {"youtube"})

    def test_youtube_contract_maps_signal_to_discovery_without_candidate(self):
        request = YouTubeSignalRequest("cozy game", "example-channel", "2026-07-01/2026-07-31")
        self.assertEqual(request.query, "cozy game")
        signal = VideoSignal("youtube", "Example video", "video", "https://youtube.example/watch?v=abc", 0.7, video_id="abc")
        discovery = SignalEvidenceMapper().map(signal)
        self.assertEqual(discovery.source_type, "signal")
        self.assertEqual(discovery.raw_reference, signal.evidence)
        self.assertEqual(discovery.metadata["signal_id"], signal.id)
        self.assertNotIn("candidate", discovery.metadata)

    def test_youtube_contract_rejects_non_video_or_invalid_confidence(self):
        with self.assertRaises(ValueError):
            VideoSignal("youtube", "x", "trend", "https://example", 0.5, video_id="x")
        with self.assertRaises(ValueError):
            VideoSignal("youtube", "x", "video", "https://example", 1.1, video_id="x")

