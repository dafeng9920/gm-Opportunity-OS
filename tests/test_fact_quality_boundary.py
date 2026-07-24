import unittest
from pathlib import Path
from tests.fact_test_support import produce_all
from evidence import EvidenceLedger
from core.schemas import EvidenceObject
class FactQualityTests(unittest.TestCase):
 def test_accepted_store_exposes_only_quality_accepted_facts(self):
  p=Path('.opportunity-os')/'quality-accepted.db'
  if p.exists(): p.unlink()
  ledger=EvidenceLedger(p); items=[]
  for i in range(5):
   e=EvidenceObject('fixture','raw',f'https://example.test/{i}'); ledger.append(e); items.append(e)
  store=produce_all(ledger,p,items)
  self.assertEqual(len(store.list_accepted_for_evidence_ids(tuple(e.id for e in items))),5)
