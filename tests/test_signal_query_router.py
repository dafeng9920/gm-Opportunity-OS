import ast
import unittest
from pathlib import Path
from adapters.youtube import YouTubeRssSignalAdapter
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component
from crawlers.runner import CrawlerContractRunner
from evidence import EvidenceLedger
from intelligence.query import SignalQuery, SignalRouter
from intelligence.sources import SourceRegistry, SourceStatus
SAMPLE = '''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><entry><title>Growth signal video</title><published>2026-07-20T10:00:00+00:00</published><yt:videoId>abc</yt:videoId></entry></feed>'''
class Backend:
    def fetch(self, target, parameters): return SAMPLE
class SignalQueryRouterTests(unittest.TestCase):
    def query(self): return SignalQuery("game", ("example",), ("video_signal",), ("youtube",), "2026-07-01/2026-07-31", {"channel_id": "UCtest", "query": "growth"})
    def test_query_contract_requires_signal_types(self):
        with self.assertRaises(ValueError): SignalQuery("game", (), ())
    def test_router_selects_registered_capability_but_executes_nothing(self):
        plans = SignalRouter().route(self.query())
        self.assertEqual(len(plans), 1); self.assertEqual(plans[0].adapter_id, "adapter.youtube-signal"); self.assertIn("no search", plans[0].limitations)
    def test_source_capability_records_youtube_limits(self):
        source = SourceRegistry().get("youtube")
        self.assertEqual(source.status, SourceStatus.ACTIVE); self.assertEqual(source.capabilities[0].supports, ("video_signal",)); self.assertIn("fixed channels", source.capabilities[0].limitations)
    def test_query_path_youtube_signal_to_discovery_to_evidence_without_candidate(self):
        adapter = YouTubeRssSignalAdapter(Backend()); plan = SignalRouter().route(self.query())[0]; request = adapter.request_from_plan(plan)
        signals = adapter.collect_signals(request); self.assertEqual(signals[0].video_id, "abc")
        database = Path('.opportunity-os') / 'query-router-test.db'
        if database.exists(): database.unlink()
        registry = ComponentRegistry(database); registry.register(Component('adapter.youtube-signal', 'YouTube RSS Signal Adapter', 'adapter', '0.1', 'active', 'test'))
        registry.register_adapter(AdapterRegistration('adapter.youtube-signal', 'mock', '0.1', 'restricted-v0', 'crawler.v0', 'active'))
        evidence = CrawlerContractRunner(registry, EvidenceLedger(database)).collect(adapter, request)
        self.assertEqual(len(evidence), 1); self.assertEqual(evidence[0].source_type, 'signal'); self.assertNotIn('candidate', evidence[0].metadata)
    def test_router_has_no_executor_agent_governance_or_gate_dependencies(self):
        tree = ast.parse(Path('intelligence/query/router.py').read_text(encoding='utf-8-sig'))
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ('adapters', 'crawlers', 'evidence', 'opportunity', 'governance', 'agents', 'candidates'):
            self.assertNotIn(forbidden, imports)
