import json, sqlite3
from pathlib import Path
from opportunity.assessments import JudgeRuntimeSource
from .contracts import RoleAssessmentRecord
class RoleAssessmentStore:
 def __init__(self,database:Path|str):
  self.db=sqlite3.connect(database); self.db.row_factory=sqlite3.Row; self.db.execute('CREATE TABLE IF NOT EXISTS role_assessments (id TEXT PRIMARY KEY, role_id TEXT, candidate_id TEXT, asset_id TEXT, judge_id TEXT, source TEXT, result TEXT, provenance TEXT, version TEXT)'); self.db.commit()
 def append(self,r): self.db.execute('INSERT INTO role_assessments VALUES (?,?,?,?,?,?,?,?,?)',(r.role_assessment_id,r.role_id,r.candidate_id,r.input_asset_id,r.judge_assessment_id,r.runtime_source.value,r.assessment_result,json.dumps(r.provenance),r.version)); self.db.commit()
 def _row(self,r): return RoleAssessmentRecord(r['id'],r['role_id'],r['candidate_id'],r['asset_id'],r['judge_id'],JudgeRuntimeSource(r['source']),r['result'],tuple(json.loads(r['provenance'])),r['version'])
 def get(self,i):
  r=self.db.execute('SELECT * FROM role_assessments WHERE id=?',(i,)).fetchone(); return self._row(r) if r else None
 def list(self): return [self._row(r) for r in self.db.execute('SELECT * FROM role_assessments ORDER BY rowid')]
