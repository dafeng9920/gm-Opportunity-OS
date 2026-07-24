from .contracts import TriadEvaluationContext, TriadContextStatus, RoleAssessmentRecord
class TriadEvaluationAssembler:
 def assemble(self,candidate_id,input_asset_id,roles,assessments,policy_version='0.1'):
  required=tuple(r.role_id for r in roles)
  if len(set(required))!=len(required): raise ValueError('required roles must be unique')
  if any(a.role_id not in required or a.candidate_id!=candidate_id or a.input_asset_id!=input_asset_id for a in assessments): raise ValueError('role assessment scope mismatch')
  if len(set(a.role_id for a in assessments))!=len(assessments): raise ValueError('duplicate role assessment')
  status=TriadContextStatus.READY if set(a.role_id for a in assessments)==set(required) else TriadContextStatus.UNKNOWN
  return TriadEvaluationContext(candidate_id,input_asset_id,tuple(assessments),required,policy_version,status)
 def role_record(self,role,assessment):
  if not assessment.candidate_id or assessment.input_asset_id=='LEGACY_UNBOUND': raise ValueError('asset-bound judge assessment required')
  return RoleAssessmentRecord(str(__import__('uuid').uuid4()),role.role_id,assessment.candidate_id,assessment.input_asset_id,assessment.assessment_id,assessment.runtime_source,assessment.assessment.recommendation.value,(assessment.judge_input_hash,),role.version)
