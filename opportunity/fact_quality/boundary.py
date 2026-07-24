from uuid import uuid4
from .contracts import FactQualityAssessment, AcceptedFact, FactLifecycleEvent, FactLifecycleStatus, QualityStatus
class FactQualityBoundary:
 def __init__(self, policies, store): self._policies=policies; self._store=store
 def assess(self, produced, artifact, policy_version='0.1'):
  self._store.append_lifecycle(FactLifecycleEvent(produced.production_id,FactLifecycleStatus.PRODUCED,'persisted produced fact'))
  self._store.append_lifecycle(FactLifecycleEvent(produced.production_id,FactLifecycleStatus.QUALITY_PENDING,'quality assessment requested'))
  policy=self._policies.get(produced.fact.fact_id,produced.fact.fact_version,policy_version)
  if policy is None: raise KeyError('fact quality policy is not registered')
  failures=[]
  if produced.measurement_artifact_id != artifact.artifact_id: failures.append('measurement artifact reference mismatch')
  if produced.fact.evidence_ids != artifact.evidence_ids: failures.append('measurement evidence lineage mismatch')
  if len(produced.fact.evidence_ids)<policy.minimum_evidence_count: failures.append('minimum evidence count not met')
  failures += [f'missing provenance: {x}' for x in policy.required_provenance if not produced.fact.provenance.get(x)]
  failures += [f'missing measurement: {x}' for x in policy.required_measurement_fields if x not in artifact.measurements]
  status=QualityStatus.PASS if not failures else QualityStatus.FAIL
  assessment=FactQualityAssessment(str(uuid4()),produced.production_id,policy.policy_id,policy.version,status,'; '.join(failures) or 'deterministic policy checks passed',produced.request_id if failures else None,'reproduce with complete evidence or measurement' if failures else None)
  self._store.append_assessment(assessment)
  if status is not QualityStatus.PASS:
   self._store.append_lifecycle(FactLifecycleEvent(produced.production_id,FactLifecycleStatus.REJECTED,assessment.assessment_reason)); return assessment,None
  accepted=AcceptedFact(str(uuid4()),produced.production_id,assessment.assessment_id,produced.fact.fact_version,produced.fact)
  self._store.append_accepted(accepted); self._store.append_lifecycle(FactLifecycleEvent(produced.production_id,FactLifecycleStatus.ACCEPTED,'quality policy passed'))
  return assessment,accepted