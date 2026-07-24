from .contracts import TriadEvaluationContext, TriadContextStatus, RoleAssessmentRecord, TriadRoleContract
from opportunity.assessments import JudgeAssessmentRecord
class TriadEvaluationAssembler:
 def assemble(self, candidate_id, input_asset_id, roles, assessments, policy_version='0.1'):
  required=tuple(role.role_id for role in roles)
  if len(set(required)) != len(required): raise ValueError('required roles must be unique')
  if any(item.role_id not in required or item.input_asset_id != input_asset_id for item in assessments): raise ValueError('role assessment scope mismatch')
  status=TriadContextStatus.READY if set(item.role_id for item in assessments)==set(required) else TriadContextStatus.UNKNOWN
  return TriadEvaluationContext(candidate_id,input_asset_id,tuple(assessments),required,policy_version,status)
 def role_record(self, role, assessment:JudgeAssessmentRecord):
  if assessment.input_asset_id=='LEGACY_UNBOUND': raise ValueError('role assessment requires asset-bound judge record')
  return RoleAssessmentRecord(str(__import__('uuid').uuid4()),role.role_id,assessment.input_asset_id,assessment.assessment_id,assessment.runtime_source,assessment.assessment.recommendation.value,(assessment.judge_input_hash,),role.version)
