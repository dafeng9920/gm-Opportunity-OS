from opportunity.assessments import JudgeRuntimeSource
from opportunity.triad_evaluation import TriadRoleContract, RoleAssessmentRecord, TriadEvaluationAssembler, TriadContextStatus

def record(role): return RoleAssessmentRecord(f'{role}-assessment',role,'candidate-1','asset-1',f'judge-{role}',JudgeRuntimeSource.STATIC_ONLY,'SMALL_SCALE_VALIDATION',('input-hash',),'0.1')
def main():
 roles=tuple(TriadRoleContract(role,role,('GateAssessmentAsset',),('GateAssessmentAsset',),('RawEvidenceWrite',),'RoleAssessmentRecord','0.1') for role in ('discovery','skeptic','commercial'))
 assembler=TriadEvaluationAssembler(); full=assembler.assemble('candidate-1','asset-1',roles,tuple(record(role.role_id) for role in roles)); missing=assembler.assemble('candidate-1','asset-1',roles,(record('discovery'),record('skeptic')))
 if full.status is not TriadContextStatus.READY or missing.status is not TriadContextStatus.UNKNOWN: raise RuntimeError('triad context status mismatch')
 print(f'Phase 18.16 runtime verified: roles={len(full.role_assessments)}, full={full.status}, missing={missing.status}')
if __name__=='__main__': main()
