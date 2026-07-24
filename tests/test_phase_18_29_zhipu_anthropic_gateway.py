import unittest
from opportunity.analysis import ZhipuAnthropicCapturedProvider, ZhipuProviderError
class ZhipuAnthropicGatewayTests(unittest.TestCase):
 def test_messages_shape_and_response_parse(self):
  def transport(body,key,timeout):
   self.assertEqual(body['model'],'glm-5.2'); self.assertIn('max_tokens',body); self.assertIn('messages',body); self.assertNotIn('response_format',body)
   return {'id':'fixture','content':[{'type':'text','text':'{"requested_fact_id":"trend_up","requested_fact_version":"0.1","measurement_artifact_ids":["m"],"evidence_ids":["e"],"analysis_summary":"review","assumptions":[],"uncertainty":[],"missing_information":[]}'}]}
  raw,payload=ZhipuAnthropicCapturedProvider(transport=transport).invoke({'candidate_id':'c','measurement_artifact_ids':['m'],'evidence_ids':['e'],'requested_fact_id':'trend_up','requested_fact_version':'0.1'})
  self.assertEqual(raw.provider_identity,'zhipu_anthropic'); self.assertEqual(payload['requested_fact_id'],'trend_up')
 def test_timeout_and_malformed_are_safe_provider_failures(self):
  req={'candidate_id':'c','measurement_artifact_ids':['m'],'evidence_ids':['e'],'requested_fact_id':'trend_up','requested_fact_version':'0.1'}
  with self.assertRaises(ZhipuProviderError): ZhipuAnthropicCapturedProvider(transport=lambda *args: (_ for _ in ()).throw(TimeoutError())).invoke(req)
  with self.assertRaises(ZhipuProviderError): ZhipuAnthropicCapturedProvider(transport=lambda *args: {'content':[]}).invoke(req)
if __name__=='__main__': unittest.main()
