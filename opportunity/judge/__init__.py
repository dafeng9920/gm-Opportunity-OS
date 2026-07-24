from .assembler import JudgeInputAssembler
from .gate_assembler import GateAssessmentJudgeInputAssembler
from .contracts import AssessmentRecommendation, JudgeAssessment, JudgeInput
from .mock_agent import DeterministicJudgeAgent
from .runner import OpportunityJudgeRunner

__all__ = [
    "AssessmentRecommendation",
    "DeterministicJudgeAgent",
    "GateAssessmentJudgeInputAssembler",
    "JudgeAssessment",
    "JudgeInput",
    "JudgeInputAssembler",
    "OpportunityJudgeRunner",
    "StaticJudgeAssessmentRuntime",
]


def __getattr__(name: str):
    if name == "StaticJudgeAssessmentRuntime":
        from .static_runtime import StaticJudgeAssessmentRuntime
        return StaticJudgeAssessmentRuntime
    raise AttributeError(name)