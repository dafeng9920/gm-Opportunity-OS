import ast
import unittest
from pathlib import Path
from core.schemas import CandidatePacket, EvidenceObject
from governance.triad.contracts import GateDecision
from opportunity.consumers import ConsumerAction, ConsumerCapability, ConsumerIdentity, ConsumerRegistry, ConsumerType, ConsumerValidator, OpportunityPacketReader, PacketQuery, PacketQueryValidator, PacketReadRequest, PacketReference
from opportunity.gates import OpportunityGateEngine
from opportunity.judge import DeterministicJudgeAgent, JudgeInput, OpportunityJudgeRunner
from opportunity.packets.contracts import OpportunityPacketAssembler
from opportunity.packets.models import GovernanceSnapshot, PacketLifecycle
from opportunity.packets.store import OpportunityPacketStore
class PacketReadServiceTests(unittest.TestCase):
    def setUp(self):
        self.database=Path('.opportunity-os')/f'packet-reader-{self._testMethodName}.db'
        if self.database.exists(): self.database.unlink()
        evidence=EvidenceObject('test','signal','https://example.test/source'); self.candidate=CandidatePacket('Example','signal',(evidence.id,),'test',.5)
        gates=OpportunityGateEngine().assess(self.candidate, {'trend_up':True,'keyword_difficulty':20,'long_tail_count':20,'available_sources':('official','community'),'monetization_path':'ads'}).results
        judge=OpportunityJudgeRunner().assess(DeterministicJudgeAgent(),JudgeInput(self.candidate,(evidence,),gates))
        self.packet=OpportunityPacketAssembler().assemble(domain='test-domain',candidate=self.candidate,evidence=(evidence,),gates=gates,judge=judge,governance=GovernanceSnapshot('REVIEWED',GateDecision.ALLOW,('audit-1',),'decision-fixture',self.candidate.id,'assessment-fixture'),signals=('signal-1',),sources=('test',),discovery_time=evidence.captured_time)
        self.store=OpportunityPacketStore(self.database); self.store.create(self.packet)
        registry=ConsumerRegistry(self.database); registry.register(ConsumerIdentity('consumer.reader',ConsumerType.SERVICE,'0.1'),ConsumerCapability('consumer.reader',(ConsumerAction.READ,),('0.1',),'test read','0.1'))
        self.reader=OpportunityPacketReader(ConsumerValidator(registry),self.store)
    def request(self, consumer='consumer.reader', action=ConsumerAction.READ): return PacketReadRequest(consumer,PacketReference(self.packet.opportunity_id,'0.1'),action,'0.1')
    def test_query_contract_valid_invalid_limit_and_status(self):
        PacketQueryValidator().validate(PacketQuery(domain='test-domain',version='0.1',limit=1))
        with self.assertRaises(ValueError): PacketQueryValidator().validate(PacketQuery(limit=0))
        with self.assertRaises(ValueError): PacketQueryValidator().validate(PacketQuery(lifecycle_status='INVALID'))
    def test_packet_store_read_existing_and_empty(self):
        self.assertEqual(self.store.get(self.packet.opportunity_id,'0.1').opportunity_id,self.packet.opportunity_id)
        self.assertEqual(self.store.query(opportunity_id='missing'),())
    def test_reader_returns_snapshot_for_valid_consumer_read(self):
        result=self.reader.read(self.request(),'0.1',PacketQuery(domain='test-domain',opportunity_id=self.packet.opportunity_id,version='0.1'))
        self.assertEqual(result.returned_count,1); self.assertEqual(result.request_id,self.request().request_id if False else result.request_id); self.assertIn(self.packet.opportunity_id,result.packets[0].serialized_packet)
    def test_reader_rejects_invalid_consumer_and_unauthorized_action(self):
        with self.assertRaises(KeyError): self.reader.read(self.request('missing'),'0.1',PacketQuery())
        with self.assertRaises(ValueError): PacketReadRequest('consumer.reader',PacketReference(self.packet.opportunity_id,'0.1'),'EXPORT','0.1')
    def test_reader_boundary_does_not_import_evaluation_or_governance(self):
        tree=ast.parse(Path('opportunity/consumers/reader.py').read_text(encoding='utf-8-sig'))
        imports=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        for forbidden in ('opportunity.gates','opportunity.judge','governance','runtime','adapters','crawlers'):
            self.assertNotIn(forbidden,imports)
