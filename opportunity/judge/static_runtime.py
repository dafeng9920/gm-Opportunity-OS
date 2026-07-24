"""Static-only deterministic runtime implementation; it never writes storage."""
from __future__ import annotations
from opportunity.assessments import JudgeRuntimeSource
from .mock_agent import DeterministicJudgeAgent
from .runner import OpportunityJudgeRunner
from .runtime_adapter import JudgeDecision, JudgeRuntimeInvocation, JudgeRuntimeResult

class StaticJudgeAssessmentRuntime:
    """Contract fixture, not a real Judge Runtime or Agent."""
    skill_id='opportunity.judge'; skill_version='v0.1'
    runtime_source=JudgeRuntimeSource.STATIC_ONLY
    runtime_id='STATIC_ONLY'; runtime_version='STATIC_ONLY'
    def __init__(self) -> None:
        self._runner=OpportunityJudgeRunner(); self._judge=DeterministicJudgeAgent()
    def execute(self, invocation: JudgeRuntimeInvocation) -> JudgeRuntimeResult:
        assessment=self._runner.assess(self._judge, invocation.judge_input)
        return JudgeRuntimeResult(JudgeDecision.REVIEW_REQUIRED, assessment, 'static-contract-fixture', self.runtime_source, self.runtime_id, self.runtime_version)
