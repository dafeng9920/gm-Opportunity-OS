import json, sqlite3
from pathlib import Path
from opportunity.assessments import JudgeRuntimeSource
from .contracts import RoleAssessmentRecord
class RoleAssessmentStore:
 def __init__(self,database:Path|str):
  self.db=sqlite3.connect(database); self.db.row_factory=sqlite3.Row; self.db.execute('CREATE TABLE IF NOT EXISTS role_assessments (id TEXT PRIMARY KEY, role_id TEXT, asset_id TEXT, judge_id TEXT, source TEXT, result TEXT, provenance TEXT, version TEXT)'); self.db.commit()
 def append(self,record:RoleAssessmentRecord):
  self.db.execute('INSERT INTO role_assessments VALUES (?,?,?,?,?,?,?,?)',(record.role_assessment_id,record.role_id,record.input_asset_id,record.judge_assessment_id,record.runtime_source.value,record.assessment_result,json.dumps(record.provenance),record.version)); self.db.commit()
 def _row(self,row): return RoleAssessmentRecord(row['id'],row['role_id'],row['asset_id'],row['judge_id'],JudgeRuntimeSource(row['source']),row['result'],tuple(json.loads(row['provenance'])),row['version'])
 def get(self,record_id):
  row=self.db.execute('SELECT * FROM role_assessments WHERE id=?',(record_id,)).fetchone(); return self._row(row) if row else None
 def list(self): return [self._row(row) for row in self.db.execute('SELECT * FROM role_assessments ORDER BY rowid').fetchall()]
