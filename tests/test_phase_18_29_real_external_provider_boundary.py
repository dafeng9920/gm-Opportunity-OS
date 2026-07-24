import os, unittest
from opportunity.analysis.external import ZhipuCapturedProvider, ZhipuProviderError
class ZhipuProviderBoundaryTests(unittest.TestCase):
 def test_fake_transport_returns_only_untrusted_payload(self):
  def transport(body, key, timeout):
   self.assertEqual(set(body['messages'][1]['content'] and __import__('json').loads(body['messages'][1]['content'])), {'candidate_id','measurement_artifact_ids','evidence_ids','requested_fact_id','requested_fact_version'})
   return {'id':'fake-response','choices':[{'message':{'content':'{"requested_fact_id":"trend_up"}'}}]}
  provider=ZhipuCapturedProvider(transport=transport)
  artifact,payload=provider.invoke({'candidate_id':'c','measurement_artifact_ids':['m'],'evidence_ids':['e'],'requested_fact_id':'trend_up','requested_fact_version':'0.1','ignored':'no'})
  self.assertEqual(artifact.provider_identity,'zhipu'); self.assertEqual(payload['requested_fact_id'],'trend_up')
 def test_malformed_and_timeout_become_provider_errors(self):
  with self.assertRaises(ZhipuProviderError): ZhipuCapturedProvider(transport=lambda *args: {'choices':[]}).invoke({'candidate_id':'c','measurement_artifact_ids':['m'],'evidence_ids':['e'],'requested_fact_id':'trend_up','requested_fact_version':'0.1'})
  with self.assertRaises(ZhipuProviderError): ZhipuCapturedProvider(transport=lambda *args: (_ for _ in ()).throw(TimeoutError())).invoke({'candidate_id':'c','measurement_artifact_ids':['m'],'evidence_ids':['e'],'requested_fact_id':'trend_up','requested_fact_version':'0.1'})
if __name__=='__main__': unittest.main()
