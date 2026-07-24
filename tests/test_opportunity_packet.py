import ast
import unittest
from pathlib import Path
from core.registry import ComponentRegistry
from core.schemas import CandidatePacket, Component, EvidenceObject
from crawlers.contract import CrawlRequest
from crawlers.runner import CrawlerContractRunner
from intelligence.signals.contracts import SignalRecord
from intelligence.signals.mapper import SignalEvidenceMapper
from evidence import EvidenceLedger
from governance.triad.contracts import GateDecision
from opportunity.gates import OpportunityGateEngine
from opportunity.judge import DeterministicJudgeAgent, JudgeInput, OpportunityJudgeRunner
from opportunity.packets.contracts import OpportunityPacketAssembler
from opportunity.packets.models import GovernanceSnapshot, NextAction, PacketLifecycle
from opportunity.packets.serializer import OpportunityPacketSerializer
from opportunity.packets.store import OpportunityPacketStore
class OpportunityPacketTests(unittest.TestCase):
    def setUp(self):
        self.evidence = EvidenceObject('youtube', 'signal', 'https://youtube.example/watch?v=abc', metadata={'signal_type':'video'})
        self.candidate = CandidatePacket('Example', 'video signal', (self.evidence.id,), 'youtube', .5)
        self.gates = OpportunityGateEngine().assess(self.candidate, {'trend_up':True,'keyword_difficulty':20,'long_tail_count':20,'available_sources':('official','community'),'monetization_path':'ads'}).results
        self.judge = OpportunityJudgeRunner().assess(DeterministicJudgeAgent(), JudgeInput(self.candidate, (self.evidence,), self.gates))
    def packet(self, version='0.1'):
        return OpportunityPacketAssembler().assemble(domain='test-domain', candidate=self.candidate, evidence=(self.evidence,), gates=self.gates, judge=self.judge, governance=GovernanceSnapshot('REVIEWED', GateDecision.ALLOW, ('triad-audit-1',), 'decision-fixture', self.candidate.id, 'assessment-fixture'), signals=('video_signal',), sources=('youtube',), discovery_time=self.evidence.captured_time, version=version)
    def test_end_to_end_fixture_assembles_referenced_output(self):
        database = Path('.opportunity-os') / 'packet-e2e.db'
        if database.exists(): database.unlink()
        signal = SignalRecord('fixture', 'Example', 'video_signal', 'https://example.test/video', .5)
        discovery = SignalEvidenceMapper().map(signal)
        class SignalCrawler:
            crawler_id = 'crawler.fixture-signal'
            def crawl(self, request): return [discovery]
        registry = ComponentRegistry(database)
        registry.register(Component('crawler.fixture-signal', 'Fixture Signal Crawler', 'crawler', '0.1', 'active', 'test-only discovery producer'))
        evidence = CrawlerContractRunner(registry, EvidenceLedger(database)).collect(SignalCrawler(), CrawlRequest('fixture', 'https://example.test'))[0]
        candidate = CandidatePacket('Example', 'video signal', (evidence.id,), 'fixture', .5)
        gates = OpportunityGateEngine().assess(candidate, {'trend_up':True,'keyword_difficulty':20,'long_tail_count':20,'available_sources':('official','community'),'monetization_path':'ads'}).results
        judge = OpportunityJudgeRunner().assess(DeterministicJudgeAgent(), JudgeInput(candidate, (evidence,), gates))
        packet = OpportunityPacketAssembler().assemble(domain='test-domain', candidate=candidate, evidence=(evidence,), gates=gates, judge=judge, governance=GovernanceSnapshot('REVIEWED', GateDecision.ALLOW, ('triad-audit-1',), 'decision-fixture', candidate.id, 'assessment-fixture'), signals=(signal.id,), sources=('fixture',), discovery_time=evidence.captured_time)
        data = OpportunityPacketSerializer().to_dict(packet)
        self.assertEqual(data['candidate_id'], candidate.id)
        self.assertEqual(data['evidence_refs'][0]['evidence_id'], evidence.id)
        self.assertEqual(data['judge']['recommendation'], 'SMALL_SCALE_VALIDATION')
        self.assertEqual(data['governance']['decision'], 'ALLOW')
    def test_lifecycle_finalized_version_is_immutable_and_new_version_is_distinct(self):
        database = Path('.opportunity-os') / 'packet-store-test.db'
        if database.exists(): database.unlink()
        store = OpportunityPacketStore(database); packet = self.packet(); store.create(packet)
        for state in (PacketLifecycle.ASSEMBLED, PacketLifecycle.ASSESSED, PacketLifecycle.GOVERNANCE_REVIEWED, PacketLifecycle.FINALIZED): store.advance(packet.opportunity_id, packet.version, state)
        with self.assertRaises(ValueError): store.advance(packet.opportunity_id, packet.version, PacketLifecycle.FINALIZED)
        revised = self.packet('0.2')
        from dataclasses import replace
        revised = replace(revised, opportunity_id=packet.opportunity_id)
        store.create(revised)
        self.assertEqual(store.lifecycle(revised.opportunity_id, '0.2'), PacketLifecycle.DRAFT)
    def test_packet_rejects_snapshot_without_derived_decision_binding(self):
        assembler = OpportunityPacketAssembler()
        with self.assertRaisesRegex(ValueError, "decision artifact"):
            assembler.assemble(domain="test-domain", candidate=self.candidate, evidence=(self.evidence,), gates=self.gates, judge=self.judge, governance=GovernanceSnapshot("REVIEWED", GateDecision.ALLOW, ("audit",)), signals=("signal",), sources=("fixture",), discovery_time=self.evidence.captured_time)
        with self.assertRaisesRegex(ValueError, "candidate"):
            assembler.assemble(domain="test-domain", candidate=self.candidate, evidence=(self.evidence,), gates=self.gates, judge=self.judge, governance=GovernanceSnapshot("REVIEWED", GateDecision.ALLOW, ("audit",), "decision-fixture", "other-candidate", "assessment-fixture"), signals=("signal",), sources=("fixture",), discovery_time=self.evidence.captured_time)
    def test_packet_boundary_has_no_system_writer_or_executor_dependencies(self):
        tree = ast.parse(Path('opportunity/packets/contracts.py').read_text(encoding='utf-8-sig'))
        imports = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ('evidence', 'runtime', 'adapters', 'crawlers', 'agents', 'architecture'):
            self.assertNotIn(forbidden, imports)


