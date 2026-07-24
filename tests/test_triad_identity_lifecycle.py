import unittest
from opportunity.triad_identity import *
class Tests(unittest.TestCase):
 def setUp(self): self.w=TriadWorker('w',('execute',),'0.1'); self.l=TriadIdentityLifecycle(self.w)
 def bind(self,role='builder',skill='s',perm=('write',),ctx=('a',)): return InvocationIdentityBinding('i-'+role,self.w.worker_id,role,skill,perm,ctx,'out','0.1')
 def test_lifecycle_release_and_reuse(self):
  self.l.assign(self.bind()); self.assertEqual(self.l.state,WorkerState.ASSIGNED); self.l.execute(); self.assertEqual(self.l.state,WorkerState.EXECUTING); self.l.release(); self.assertEqual(self.l.state,WorkerState.WHITE_STATE); self.assertIsNone(self.l.binding); self.l.assign(self.bind('skeptic','review',(),('b',))); self.assertEqual(self.l.binding.role_id,'skeptic')
 def test_cleanup_failure_and_double_release(self):
  self.l.assign(self.bind()); self.l.execute(); self.assertIsNone(self.l.release(False)); self.assertEqual(self.l.state,WorkerState.RELEASE_FAILED); self.l.release(); self.assertEqual(self.l.state,WorkerState.WHITE_STATE); self.assertIsNone(self.l.release())
if __name__=='__main__': unittest.main()
