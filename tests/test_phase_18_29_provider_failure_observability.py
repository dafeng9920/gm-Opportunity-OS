import ast, unittest, urllib.error
from pathlib import Path
from opportunity.analysis.external import ProviderFailureAudit, ProviderFailureAuditStore, ZhipuAnthropicCapturedProvider, ZhipuProviderError
class ProviderFailureObservabilityTests(unittest.TestCase):
 def test_http_failure_has_safe_classification_and_persists_no_secret_fields(self):
  def transport(*args): raise urllib.error.HTTPError('https://open.bigmodel.cn/api/anthropic/v1/messages',429,'',None,None)
  req={'candidate_id':'c','measurement_artifact_ids':['m'],'evidence_ids':['e'],'requested_fact_id':'trend_up','requested_fact_version':'0.1'}
  with self.assertRaises(ZhipuProviderError) as caught: ZhipuAnthropicCapturedProvider(transport=transport).invoke(req)
  err=caught.exception; audit=ProviderFailureAudit('zhipu_anthropic',err.endpoint or '', 'glm-5.2',err.transport_stage,err.category,err.http_status,err.timeout_class)
  self.assertEqual(audit.http_status,429); self.assertEqual(audit.transport_stage,'response_received'); self.assertNotIn('key',audit.__dataclass_fields__); self.assertNotIn('authorization',audit.__dataclass_fields__)
  p=Path('.opportunity-os/phase-18.29-failure-audit.db'); p.unlink(missing_ok=True); ProviderFailureAuditStore(p).append(audit)
 def test_failure_observability_module_has_no_governance_imports(self):
  tree=ast.parse(Path('opportunity/analysis/external.py').read_text(encoding='utf-8-sig')); imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
  for bad in ('opportunity.facts','opportunity.fact_quality','opportunity.gate_evaluation','opportunity.judge','opportunity.triad_evaluation'): self.assertNotIn(bad,imports)
if __name__=='__main__': unittest.main()
