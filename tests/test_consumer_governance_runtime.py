import ast
import unittest
from pathlib import Path
from opportunity.consumers import ConsumerAccessRequest, ConsumerAccessRuntime, ConsumerAction, ConsumerAuditDecision, ConsumerAuditStore, ConsumerCapability, ConsumerIdentity, ConsumerPolicy, ConsumerPolicyGate, ConsumerRegistry, ConsumerType, PacketReference
class ConsumerGovernanceRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.db=Path('.opportunity-os')/f'consumer-governance-{self._testMethodName}.db'
        if self.db.exists(): self.db.unlink()
        registry=ConsumerRegistry(self.db); registry.register(ConsumerIdentity('consumer.service',ConsumerType.SERVICE,'0.1'),ConsumerCapability('consumer.service',(ConsumerAction.READ,),('0.1',),'read packet','0.1'))
        self.registry=registry; self.policy=ConsumerPolicy('policy.service-read','SERVICE',(ConsumerAction.READ,),('0.1',),'0.1')
    def request(self, consumer='consumer.service', version='0.1', action=ConsumerAction.READ): return ConsumerAccessRequest(consumer,action,PacketReference('packet-1',version),'0.1')
    def test_access_request_valid_and_invalid_action(self):
        self.assertEqual(self.request().action,ConsumerAction.READ)
        with self.assertRaises(ValueError): ConsumerAccessRequest('consumer.service','EXPORT',PacketReference('packet-1','0.1'),'0.1')
    def test_policy_gate_allow_deny_and_review_required(self):
        gate=ConsumerPolicyGate(self.registry,self.policy)
        self.assertEqual(gate.decide(self.request(),'0.1').decision,ConsumerAuditDecision.ALLOW)
        self.assertEqual(gate.decide(self.request('missing'),'0.1').decision,ConsumerAuditDecision.DENY)
        self.assertEqual(gate.decide(self.request(version='0.2'),'0.1').decision,ConsumerAuditDecision.DENY)
        review=ConsumerPolicy('policy.human-read','HUMAN',(ConsumerAction.READ,),('0.1',),'0.1')
        self.assertEqual(ConsumerPolicyGate(self.registry,review).decide(self.request(),'0.1').decision,ConsumerAuditDecision.REVIEW_REQUIRED)
    def test_policy_gate_denies_policy_unsupported_action_model(self):
        deny_policy=ConsumerPolicy('policy.no-actions','SERVICE',(),('0.1',),'0.1')
        self.assertEqual(ConsumerPolicyGate(self.registry,deny_policy).decide(self.request(),'0.1').reason_code,'ACTION_NOT_ALLOWED')
    def test_access_runtime_audits_every_decision_and_store_lists_them(self):
        audit=ConsumerAuditStore(self.db); runtime=ConsumerAccessRuntime(ConsumerPolicyGate(self.registry,self.policy),audit)
        allowed=runtime.decide(self.request(),'0.1'); denied=runtime.decide(self.request('missing'),'0.1')
        events=audit.list()
        self.assertEqual((allowed.decision,denied.decision),(ConsumerAuditDecision.ALLOW,ConsumerAuditDecision.DENY))
        self.assertEqual([event.decision for event in events],[ConsumerAuditDecision.ALLOW,ConsumerAuditDecision.DENY])
    def test_policy_gate_is_independent_of_runtime_evaluation_governance_and_skills(self):
        tree=ast.parse(Path('opportunity/consumers/policy_gate.py').read_text(encoding='utf-8-sig'))
        imports=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        for forbidden in ('runtime','opportunity.gates','opportunity.judge','governance','crawlers','skills','adapters'):
            self.assertNotIn(forbidden,imports)
