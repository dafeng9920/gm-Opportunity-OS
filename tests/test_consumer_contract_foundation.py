import ast
import sqlite3
import unittest
from pathlib import Path
from opportunity.consumers import ConsumerAction, ConsumerAuditDecision, ConsumerAuditEvent, ConsumerCapability, ConsumerIdentity, ConsumerRegistry, ConsumerType, ConsumerValidator, PacketReadRequest, PacketReference
class ConsumerFoundationTests(unittest.TestCase):
    def identity(self): return ConsumerIdentity('consumer.fixture',ConsumerType.SERVICE,'0.1')
    def capability(self, versions=('0.1',)): return ConsumerCapability('consumer.fixture',(ConsumerAction.READ,),versions,'test read only','0.1')
    def registry(self):
        path=Path('.opportunity-os')/f'consumer-registry-{self._testMethodName}.db'
        if path.exists():path.unlink()
        registry=ConsumerRegistry(path); registry.register(self.identity(),self.capability()); return registry
    def request(self, version='0.1', action=ConsumerAction.READ): return PacketReadRequest('consumer.fixture',PacketReference('packet-1',version),action,version)
    def test_identity_valid_invalid_id_and_invalid_type(self):
        self.assertEqual(self.identity().consumer_type,ConsumerType.SERVICE)
        with self.assertRaises(ValueError): ConsumerIdentity('',ConsumerType.HUMAN,'0.1')
        with self.assertRaises(ValueError): ConsumerIdentity('x','UNKNOWN','0.1')
    def test_capability_allows_read_and_rejects_unknown_action(self):
        self.assertEqual(self.capability().allowed_actions,(ConsumerAction.READ,))
        with self.assertRaises(ValueError): ConsumerCapability('consumer.fixture',('EXPORT',),('0.1',),'x','0.1')
    def test_read_request_valid_invalid_consumer_and_invalid_action(self):
        validator=ConsumerValidator(self.registry()); validator.validate_read_request(self.request(),'0.1')
        with self.assertRaises(KeyError): validator.validate_read_request(PacketReadRequest('missing',PacketReference('packet-1','0.1'),ConsumerAction.READ,'0.1'),'0.1')
        with self.assertRaises(ValueError): PacketReadRequest('consumer.fixture',PacketReference('packet-1','0.1'),'EXPORT','0.1')
    def test_read_request_rejects_unallowed_packet_or_contract_version(self):
        validator=ConsumerValidator(self.registry())
        with self.assertRaises(PermissionError): validator.validate_read_request(self.request('0.2'),'0.1')
        with self.assertRaises(ValueError): validator.validate_read_request(PacketReadRequest('consumer.fixture',PacketReference('packet-1','0.1'),ConsumerAction.READ,'0.2'),'0.1')
    def test_registry_register_duplicate_reject_and_lookup(self):
        registry=self.registry(); identity=registry.get_identity('consumer.fixture','0.1'); self.assertEqual((identity.consumer_id,identity.consumer_type,identity.version),('consumer.fixture',ConsumerType.SERVICE,'0.1')); self.assertEqual(registry.get_capability('consumer.fixture','0.1'),self.capability())
        with self.assertRaises(sqlite3.IntegrityError): registry.register(self.identity(),self.capability())
    def test_consumer_audit_contract_and_boundary_dependencies(self):
        self.assertEqual(ConsumerAuditEvent('consumer.fixture','packet-1','0.1',ConsumerAction.READ,ConsumerAuditDecision.ALLOW).decision,ConsumerAuditDecision.ALLOW)
        tree=ast.parse(Path('opportunity/consumers/validator.py').read_text(encoding='utf-8-sig'))
        imports=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        for forbidden in ('skills','runtime','evidence','candidates','adapters','governance','opportunity.packets'):
            self.assertNotIn(forbidden,imports)


