import unittest
from pathlib import Path
from uuid import uuid4
from opportunity.assessments import JudgeRuntimeSource
from opportunity.triad_evaluation import RoleAssessmentRecord, TriadEvaluationAssembler, TriadRoleContract
from opportunity.triad_evaluation.store import RoleAssessmentStore
from opportunity.triad_evaluation.decision_store import TriadDecisionStore
from opportunity.triad_evaluation.decision_writer import TriadDecisionArtifactWriter
from opportunity.triad_evaluation.decisions import AgreementStatus,TriadDecisionStatus
class Tests(unittest.TestCase):
 def setUp(self):
  self.db=Path('.opportunity-os')/f'triad-decision-{self._testMethodName}.db'; self.db.unlink(missing_ok=True); self.roles=tuple(TriadRoleContract(x,x,('asset',),('asset',),('raw',),'role','0.1') for x in ('discovery','skeptic','commercial')); self.rs=RoleAssessmentStore(self.db); self.ds=TriadDecisionStore(self.db); self.a=TriadEvaluationAssembler(); self.w=TriadDecisionArtifactWriter(self.rs,self.ds)
 def rec(self,role,result='SUPPORT',candidate='c',asset='a'): return RoleAssessmentRecord(role+'-'+str(uuid4()),role,candidate,asset,'judge-'+role,JudgeRuntimeSource.STATIC_ONLY,result,('hash',),'0.1')
 def context(self,items): return self.a.assemble('c','a',self.roles,items)
 def test_consensus_and_roundtrip(self):
  items=tuple(self.rec(x.role_id) for x in self.roles); [self.rs.append(x) for x in items]; out=self.w.write(self.context(items)); self.assertEqual((out.agreement_status,out.decision_status),(AgreementStatus.CONSENSUS,TriadDecisionStatus.READY)); self.assertEqual(self.ds.get(out.artifact_id),out); self.assertEqual(self.ds.list_by_candidate('c'),[out])
 def test_missing_conflict_and_unpersisted(self):
  two=(self.rec('discovery'),self.rec('skeptic')); [self.rs.append(x) for x in two]; self.assertEqual(self.w.write(self.context(two)).decision_status,TriadDecisionStatus.UNKNOWN)
  items=(self.rec('discovery','SUPPORT'),self.rec('skeptic','REJECT'),self.rec('commercial','SUPPORT')); [self.rs.append(x) for x in items]; self.assertEqual(self.w.write(self.context(items)).decision_status,TriadDecisionStatus.REVIEW_REQUIRED)
  un=(self.rec('discovery'),); self.assertRaisesRegex(ValueError,'unpersisted',self.w.write,self.context(un))
 def test_append_only_and_mismatch(self):
  self.assertFalse(hasattr(self.ds,'update')); self.assertFalse(hasattr(self.ds,'delete'))
  bad=self.rec('discovery',candidate='other'); self.rs.append(bad); self.assertRaisesRegex(ValueError,'scope mismatch',self.context,(bad,))
 def test_input_asset_and_legacy_are_rejected(self):
  foreign = self.rec('discovery', asset='other')
  self.rs.append(foreign)
  with self.assertRaisesRegex(ValueError, 'scope mismatch'):
      self.a.assemble('c', 'a', self.roles, (foreign,))
  with self.assertRaises(ValueError):
      RoleAssessmentRecord('legacy','discovery','','','judge',JudgeRuntimeSource.STATIC_ONLY,'SUPPORT',(), '0.1')

 def test_duplicate_artifact_identity_rejected(self):
  items = tuple(self.rec(x.role_id) for x in self.roles)
  [self.rs.append(x) for x in items]
  artifact = self.w.write(self.context(items))
  with self.assertRaises(Exception):
      self.ds.append(artifact)

if __name__=='__main__': unittest.main()
