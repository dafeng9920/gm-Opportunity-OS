from .contracts import WorkerState,InvocationIdentityBinding,IdentityReleaseRecord
class TriadIdentityLifecycle:
 def __init__(self,worker): self.worker=worker; self.state=WorkerState.WHITE_STATE; self.binding=None; self.releases=[]
 def assign(self,binding):
  if self.state is not WorkerState.WHITE_STATE or binding.worker_id!=self.worker.worker_id: raise ValueError('worker is not available')
  self.binding=binding; self.state=WorkerState.ASSIGNED
 def execute(self):
  if self.state is not WorkerState.ASSIGNED: raise ValueError('worker is not assigned')
  self.state=WorkerState.EXECUTING
 def release(self,cleanup_ok=True):
  if self.state is WorkerState.WHITE_STATE: return None
  if self.state not in (WorkerState.ASSIGNED,WorkerState.EXECUTING,WorkerState.RELEASE_FAILED): raise ValueError('worker cannot release')
  self.state=WorkerState.RELEASING
  if not cleanup_ok: self.state=WorkerState.RELEASE_FAILED; return None
  from uuid import uuid4
  record=IdentityReleaseRecord(str(uuid4()),self.binding.invocation_id,self.worker.worker_id,'CLEAN',self.binding.version); self.releases.append(record); self.binding=None; self.state=WorkerState.WHITE_STATE; return record
