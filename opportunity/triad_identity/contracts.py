from dataclasses import dataclass,field
from enum import StrEnum
from uuid import uuid4
class WorkerState(StrEnum): WHITE_STATE='WHITE_STATE'; ASSIGNED='ASSIGNED'; EXECUTING='EXECUTING'; RELEASING='RELEASING'; RELEASE_FAILED='RELEASE_FAILED'
@dataclass(frozen=True,slots=True)
class TriadWorker:
 worker_id:str; base_capabilities:tuple[str,...]; version:str; lifecycle_state:WorkerState=WorkerState.WHITE_STATE
@dataclass(frozen=True,slots=True)
class InvocationIdentityBinding:
 invocation_id:str; worker_id:str; role_id:str; skill_id:str; permission_scope:tuple[str,...]; input_scope:tuple[str,...]; output_contract:str; version:str; expires_at:str|None=None
@dataclass(frozen=True,slots=True)
class IdentityReleaseRecord:
 release_id:str; invocation_id:str; worker_id:str; cleanup_status:str; version:str
