"""Reproducible small-scope live YouTube RSS integration evidence."""
from pathlib import Path
from adapters import YouTubeRssSignalAdapter
from core.registry import ComponentRegistry
from core.schemas import AdapterRegistration, Component, RuntimeRegistration
from crawlers.contract import CrawlRequest
from crawlers.runner import CrawlerContractRunner
from evidence import EvidenceLedger
from runtime.audit import AuditLog
from runtime.bridges import SandboxedFetchBackend
from runtime.manager import RuntimeManager
from runtime.real_workers import SubprocessScraplingWorker

def main() -> None:
    root = Path('.opportunity-os'); db = root / 'phase12-youtube.db'
    if db.exists(): db.unlink()
    registry = ComponentRegistry(db)
    registry.register(Component('adapter.youtube-signal', 'YouTube RSS Signal Adapter', 'adapter', '0.1', 'active', 'public channel RSS to signal discovery'))
    registry.register(Component('runtime.scrapling-venv', 'Scrapling Runtime', 'runtime', '0.4.11', 'active', 'pinned subprocess runtime'))
    registry.register_adapter(AdapterRegistration('adapter.youtube-signal', 'scrapling@0.4.11', '0.1', 'restricted-v0', 'crawler.v0', 'active'))
    registry.register_runtime(RuntimeRegistration('runtime.scrapling-venv', 'Scrapling Worker', 'subprocess', '0.4.11', 'restricted-v0', 'available'))
    manager = RuntimeManager(registry, AuditLog(db))
    worker = SubprocessScraplingWorker(root / 'venvs' / 'scrapling' / 'Scripts' / 'python.exe', Path('runtime/youtube_rss_worker.py'))
    backend = SandboxedFetchBackend(manager, worker, 'runtime.scrapling-venv', ('www.youtube.com',), 'scrapling@0.4.11', 'adapter.youtube-signal')
    adapter = YouTubeRssSignalAdapter(backend)
    request = CrawlRequest('youtube', 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_x5XG1OV2P6uZZ5FSM9Ttw', {'time_window': '2000-01-01/2100-01-01'})
    evidence = CrawlerContractRunner(registry, EvidenceLedger(db)).collect(adapter, request)
    audit = AuditLog(db).list()
    print({'evidence_count': len(evidence), 'runtime_id': audit[-1].runtime_id, 'adapter_id': audit[-1].adapter_id, 'version': audit[-1].external_version, 'decision': audit[-1].decision, 'output_hash': audit[-1].output_hash})
if __name__ == '__main__': main()

