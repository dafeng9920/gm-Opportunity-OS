from .assembler import JudgeInputAssembler
from .gate_assembler import GateAssessmentJudgeInputAssembler
from .contracts import AssessmentRecommendation, JudgeAssessment, JudgeInput
from .mock_agent import DeterministicJudgeAgent
from .runner import OpportunityJudgeRunner
__all__=['AssessmentRecommendation','DeterministicJudgeAgent','GateAssessmentJudgeInputAssembler','JudgeAssessment','JudgeInput','JudgeDecision','JudgeRuntimeAdapter','JudgeRuntimeInvocation','JudgeRuntimeResult','JudgeInputAssembler','OpportunityJudgeRunner','StaticJudgeAssessmentRuntime']
def __getattr__(name: str):
    if name == 'StaticJudgeAssessmentRuntime':
        from .static_runtime import StaticJudgeAssessmentRuntime
        return StaticJudgeAssessmentRuntime
    if name in {'JudgeDecision','JudgeRuntimeAdapter','JudgeRuntimeInvocation','JudgeRuntimeResult'}:
        from .runtime_adapter import JudgeDecision, JudgeRuntimeAdapter, JudgeRuntimeInvocation, JudgeRuntimeResult
        return {'JudgeDecision':JudgeDecision,'JudgeRuntimeAdapter':JudgeRuntimeAdapter,'JudgeRuntimeInvocation':JudgeRuntimeInvocation,'JudgeRuntimeResult':JudgeRuntimeResult}[name]
    raise AttributeError(name)
