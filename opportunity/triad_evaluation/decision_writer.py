from .decisions import AgreementStatus, ConflictReference, TriadDecisionArtifact, TriadDecisionStatus
class TriadDecisionArtifactWriter:
 def __init__(self,role_store,decision_store): self.role_store=role_store; self.decision_store=decision_store
 def write(self,context):
  refs=tuple(x.role_assessment_id for x in context.role_assessments)
  if len(set(refs))!=len(refs): raise ValueError('duplicate role assessment')
  items=[]
  for ref in refs:
   stored=self.role_store.get(ref)
   if stored is None: raise ValueError('unpersisted role assessment')
   if not stored.candidate_id or not stored.input_asset_id or not stored.provenance: raise ValueError('legacy_unbound role assessment')
   items.append(stored)
  if any(x.candidate_id!=context.candidate_id for x in items): raise ValueError('candidate mismatch')
  if any(x.input_asset_id!=context.input_asset_id for x in items): raise ValueError('input asset mismatch')
  required=set(context.required_roles); actual={x.role_id for x in items}
  if any(x.role_id not in required for x in items): raise ValueError('unauthorized role')
  missing=required-actual
  if missing: a=TriadDecisionArtifact(context.candidate_id,context.context_id,context.input_asset_id,refs,context.required_roles,AgreementStatus.INCOMPLETE,TriadDecisionStatus.UNKNOWN,tuple('missing_role:'+x for x in sorted(missing)),(),context.policy_version,'0.1')
  else:
   values={x.assessment_result for x in items}
   if len(values)>1:
    conflicts=tuple(ConflictReference(items[0].role_id,x.role_id,'assessment_result',items[0].assessment_result,x.assessment_result,'role_result_conflict') for x in items[1:] if x.assessment_result!=items[0].assessment_result); a=TriadDecisionArtifact(context.candidate_id,context.context_id,context.input_asset_id,refs,context.required_roles,AgreementStatus.CONFLICT,TriadDecisionStatus.REVIEW_REQUIRED,('role_result_conflict',),conflicts,context.policy_version,'0.1')
   else: a=TriadDecisionArtifact(context.candidate_id,context.context_id,context.input_asset_id,refs,context.required_roles,AgreementStatus.CONSENSUS,TriadDecisionStatus.READY,(),(),context.policy_version,'0.1')
  self.decision_store.append(a); return a
