import json, sqlite3
from pathlib import Path
from contextlib import contextmanager
from opportunity.evaluation.contracts import EvaluationFact, EvaluationFactCategory, FactVerification
from .contracts import FactQualityAssessment, AcceptedFact, FactLifecycleEvent
class FactQualityStore:
 def __init__(self,database:Path|str):
  self.database=str(database)
  with self._session() as db:
   db.execute('CREATE TABLE IF NOT EXISTS fact_quality_assessments (id TEXT PRIMARY KEY, fact_id TEXT, policy_id TEXT, policy_version TEXT, status TEXT, reason TEXT, rework TEXT, action TEXT, created_at TEXT)')
   db.execute('CREATE TABLE IF NOT EXISTS accepted_facts (id TEXT PRIMARY KEY, source_fact_id TEXT, assessment_id TEXT, version TEXT, fact_name TEXT, category TEXT, value TEXT, evidence_ids TEXT, confidence REAL, provenance TEXT, accepted_at TEXT)')
   db.execute('CREATE TABLE IF NOT EXISTS fact_lifecycle (fact_id TEXT, status TEXT, reason TEXT, created_at TEXT)')
 @contextmanager
 def _session(self):
  c=sqlite3.connect(self.database); c.row_factory=sqlite3.Row
  try: yield c; c.commit()
  finally: c.close()
 def append_assessment(self,a):
  with self._session() as db: db.execute('INSERT INTO fact_quality_assessments VALUES (?,?,?,?,?,?,?,?,?)',(a.assessment_id,a.source_fact_id,a.policy_id,a.policy_version,a.status.value,a.assessment_reason,a.rework_reference,a.recommended_action,a.created_at))
 def append_lifecycle(self,e):
  with self._session() as db: db.execute('INSERT INTO fact_lifecycle VALUES (?,?,?,?)',(e.source_fact_id,e.status.value,e.reason,e.created_at))
 def append_accepted(self,a):
  f=a.fact
  with self._session() as db: db.execute('INSERT INTO accepted_facts VALUES (?,?,?,?,?,?,?,?,?,?,?)',(a.accepted_fact_id,a.source_fact_id,a.quality_assessment_id,a.accepted_version,f.fact_id,f.category.value,json.dumps(f.value),json.dumps(f.evidence_ids),f.confidence,json.dumps(dict(f.provenance)),a.accepted_at))
 def list_for_evidence_ids(self,ids):
  allowed=set(ids)
  with self._session() as db: rows=db.execute('SELECT * FROM accepted_facts ORDER BY accepted_at,id').fetchall()
  return tuple(EvaluationFact(r['fact_name'],EvaluationFactCategory(r['category']),json.loads(r['value']),tuple(json.loads(r['evidence_ids'])),r['confidence'],FactVerification.EVIDENCE_BACKED,r['version'],json.loads(r['provenance'])) for r in rows if set(json.loads(r['evidence_ids'])).issubset(allowed))