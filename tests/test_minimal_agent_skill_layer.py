import ast
import unittest
from pathlib import Path
from core.schemas import CandidatePacket, EvidenceObject
from opportunity.gates import OpportunityGateEngine
from opportunity.judge import AssessmentRecommendation, JudgeAssessment, JudgeInput
from skills import SkillInvocation, SkillOutputValidator, SkillPackage, SkillRegistry, SkillStatus
class SkillLayerTests(unittest.TestCase):
    def package(self): return SkillPackage('opportunity.judge','Opportunity Judge','v0.1','Explain supplied facts','JudgeInput v0.1','JudgeAssessment v0.1',('read provided context','produce structured output'),('modify Evidence','modify Candidate','bypass Gate','call Triad directly','change Runtime policy','create state'),'skills/prompts/opportunity-judge.md')
    def assessment(self):
        evidence=EvidenceObject('test','signal','https://example.test/source'); candidate=CandidatePacket('Example','signal',(evidence.id,),'test',.5)
        gates=OpportunityGateEngine().assess(candidate, {'trend_up':True,'keyword_difficulty':20,'long_tail_count':20,'available_sources':('official','community'),'monetization_path':'ads'}).results
        return JudgeAssessment(candidate.id,'Explanation',(),AssessmentRecommendation.SMALL_SCALE_VALIDATION,(evidence.id,),tuple(f'{item.gate}@{item.version}' for item in gates))
    def test_skill_registry_is_versioned_source_of_truth(self):
        database=Path('.opportunity-os')/'skill-registry-test.db'
        if database.exists(): database.unlink()
        registry=SkillRegistry(database); package=self.package(); registry.register(package)
        self.assertEqual(registry.get('opportunity.judge','v0.1'),package)
    def test_minimal_prompt_contains_no_rules_business_or_permission_policy(self):
        prompt=Path('skills/prompts/opportunity-judge.md').read_text(encoding='utf-8-sig').lower()
        self.assertLessEqual(len(prompt.split()), 20)
        for prohibited in ('keyword_difficulty','trend_up','allow','block','runtime policy','business'):
            self.assertNotIn(prohibited,prompt)
    def test_invocation_validates_existing_judge_output_contract(self):
        invocation=SkillInvocation('opportunity.judge','judge-input:fixture','task-1',('evidence:fixture',),'restricted-v0')
        self.assertIs(SkillOutputValidator().validate(invocation,self.assessment()).__class__,JudgeAssessment)
        with self.assertRaises(ValueError): SkillOutputValidator().validate(invocation,{'assessment':'free text'})
    def test_skill_layer_has_no_core_writer_or_agent_runtime_dependencies(self):
        tree=ast.parse(Path('skills/contracts/validator.py').read_text(encoding='utf-8-sig'))
        imports=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        for forbidden in ('evidence','candidates','runtime','adapters','governance','agents','crawlers'):
            self.assertNotIn(forbidden,imports)
