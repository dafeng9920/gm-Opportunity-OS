from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4
from opportunity.assessments import JudgeAssessmentRecord, JudgeRuntimeSource

class TriadContextStatus(StrEnum): READY='READY'; UNKNOWN='UNKNOWN'
@dataclass(frozen=True, slots=True)
class TriadRoleContract:
    role_id:str; role_type:str; scope:tuple[str,...]; allowed_inputs:tuple[str,...]; forbidden_inputs:tuple[str,...]; output_contract:str; version:str
    def __post_init__(self):
        if not all((self.role_id,self.role_type,self.scope,self.allowed_inputs,self.forbidden_inputs,self.output_contract,self.version)): raise ValueError('role contract is incomplete')
@dataclass(frozen=True, slots=True)
class RoleAssessmentRecord:
    role_assessment_id:str; role_id:str; input_asset_id:str; judge_assessment_id:str; runtime_source:JudgeRuntimeSource; assessment_result:str; provenance:tuple[str,...]; version:str
    def __post_init__(self):
        if not all((self.role_assessment_id,self.role_id,self.input_asset_id,self.judge_assessment_id,self.assessment_result,self.provenance,self.version)): raise ValueError('role assessment is incomplete')
        if not isinstance(self.runtime_source,JudgeRuntimeSource): raise ValueError('role runtime source is invalid')
@dataclass(frozen=True, slots=True)
class TriadEvaluationContext:
    candidate_id:str; input_asset_id:str; role_assessments:tuple[RoleAssessmentRecord,...]; required_roles:tuple[str,...]; policy_version:str; status:TriadContextStatus; context_id:str=field(default_factory=lambda:str(uuid4()))
@dataclass(frozen=True, slots=True)
class TriadDecisionArtifactBoundary:
    context_id:str; candidate_id:str; input_asset_id:str; version:str
