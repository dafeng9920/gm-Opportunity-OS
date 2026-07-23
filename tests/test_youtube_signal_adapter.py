import unittest
from adapters.youtube import YouTubeRssSignalAdapter
from crawlers.contract import CrawlRequest
SAMPLE = '''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015"><entry><title>Roblox Codes Guide</title><published>2026-07-20T10:00:00+00:00</published><yt:videoId>abc</yt:videoId></entry></feed>'''
class Backend:
    def fetch(self, target, parameters): return SAMPLE
class YoutubeAdapterTests(unittest.TestCase):
    def request(self, **parameters): return CrawlRequest('youtube', 'https://www.youtube.com/feeds/videos.xml?channel_id=UCtest', parameters)
    def test_public_rss_maps_to_signal_discovery_record(self):
        records = YouTubeRssSignalAdapter(Backend()).crawl(self.request(query='roblox', time_window='2026-07-01/2026-07-31'))
        self.assertEqual(len(records), 1); self.assertEqual(records[0].source_type, 'signal'); self.assertEqual(records[0].metadata['video_id'], 'abc')
    def test_query_and_window_filter_without_external_search(self):
        self.assertEqual(YouTubeRssSignalAdapter(Backend()).crawl(self.request(query='other')), [])
        self.assertEqual(YouTubeRssSignalAdapter(Backend()).crawl(self.request(time_window='2026-06-01/2026-06-30')), [])
    def test_adapter_rejects_non_rss_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'RSS'):
            YouTubeRssSignalAdapter(Backend()).crawl(CrawlRequest('youtube', 'https://www.youtube.com/results?search_query=roblox'))
