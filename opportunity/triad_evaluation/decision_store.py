import sqlite3,json
from dataclasses import asdict
from pathlib import Path
from .decisions import TriadDecisionArtifact,AgreementStatus,TriadDecisionStatus,ConflictReference
class TriadDecisionStore:
 def __init__(self,database:Path|str): self.db=sqlite3.connect(database); self.db.row_factory=sqlite3.Row; self.db.execute('CREATE TABLE IF NOT EXISTS opportunity_triad_decisions (id TEXT PRIMARY KEY, payload TEXT)'); self.db.commit()
 def append(self,a): self.db.execute('INSERT INTO opportunity_triad_decisions VALUES (?,?)',(a.artifact_id,json.dumps(asdict(a),default=lambda x:x.value))); self.db.commit()
 def _row(self,r):
  p=json.loads(r['payload']); return TriadDecisionArtifact(p['candidate_id'],p['triad_context_id'],p['input_asset_id'],tuple(p['role_assessment_refs']),tuple(p['required_role_ids']),AgreementStatus(p['agreement_status']),TriadDecisionStatus(p['decision_status']),tuple(p['reason_codes']),tuple(ConflictReference(**x) for x in p['conflict_refs']),p['policy_version'],p['schema_version'],p['artifact_id'])
 def get(self,id):
  r=self.db.execute('SELECT * FROM opportunity_triad_decisions WHERE id=?',(id,)).fetchone(); return self._row(r) if r else None
 def list(self): return [self._row(r) for r in self.db.execute('SELECT * FROM opportunity_triad_decisions ORDER BY rowid')]
 def list_by_candidate(self,candidate_id): return [a for a in self.list() if a.candidate_id==candidate_id]
