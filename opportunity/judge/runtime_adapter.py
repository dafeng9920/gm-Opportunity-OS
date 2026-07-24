"""Judge runtime invocation contracts and controlled adapter; no external runtime integration."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from opportunity.assessments import AssessmentRecordSource, AssessmentRecordWriter, JudgeAssessmentRecord, JudgeInputHasher, JudgeRuntimeSource
from opportunity.gate_evaluation import GateAssessmentAsset
from .contracts import JudgeAssessment, JudgeInput
from .gate_assembler import GateAssessmentJudgeInputAssembler

class JudgeDecision(StrEnum):
    PASS='PASS'; FAIL='FAIL'; REVIEW_REQUIRED='REVIEW_REQUIRED'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True, slots=True)
class JudgeRuntimeInvocation:
    judge_input_id: str
    gate_assessment_asset_id: str
    candidate_id: str
    fact_refs: tuple[str, ...]
    runtime_context: tuple[tuple[str, str], ...]
    judge_input: JudgeInput

@dataclass(frozen=True, slots=True)
class JudgeRuntimeResult:
    decision: JudgeDecision
    assessment: JudgeAssessment
    reasoning_reference: str
    runtime_source: JudgeRuntimeSource
    runtime_id: str
    runtime_version: str

class JudgeRuntime(Protocol):
    runtime_source: JudgeRuntimeSource
    runtime_id: str
    runtime_version: str
    skill_id: str
    skill_version: str
    def execute(self, invocation: JudgeRuntimeInvocation) -> JudgeRuntimeResult: ...

class JudgeRuntimeAdapter:
    """Only path from a persisted Gate Asset through a declared Judge Runtime to assessment storage."""
    def __init__(self, assembler: GateAssessmentJudgeInputAssembler, writer: AssessmentRecordWriter, runtime: JudgeRuntime) -> None:
        self._assembler, self._writer, self._runtime = assembler, writer, runtime

    def assess(self, asset: GateAssessmentAsset) -> JudgeAssessmentRecord:
        judge_input = self._assembler.assemble(asset)
        invocation = JudgeRuntimeInvocation(JudgeInputHasher.hash(judge_input), asset.asset_id, asset.candidate_id, asset.fact_refs, (("gate_policy", f"{asset.gate_policy_id}@{asset.gate_policy_version}"),), judge_input)
        result = self._runtime.execute(invocation)
        if not isinstance(result, JudgeRuntimeResult): raise TypeError('judge runtime must return JudgeRuntimeResult')
        if result.runtime_source is not self._runtime.runtime_source: raise ValueError('judge runtime source declaration mismatch')
        if result.runtime_id != self._runtime.runtime_id or result.runtime_version != self._runtime.runtime_version: raise ValueError('judge runtime metadata mismatch')
        if result.assessment.candidate_id != asset.candidate_id: raise ValueError('judge runtime assessment candidate mismatch')
        if not result.reasoning_reference: raise ValueError('judge runtime requires reasoning reference')
        record = JudgeAssessmentRecord(judge_input_hash=invocation.judge_input_id, candidate_id=asset.candidate_id, assessment=result.assessment, evidence_refs=tuple(item.id for item in judge_input.evidence), gate_refs=tuple(f'{item.gate}@{item.version}' for item in judge_input.gate_results), skill_id=self._runtime.skill_id, skill_version=self._runtime.skill_version, runtime_id=result.runtime_id, runtime_version=result.runtime_version, audit_refs=(), source=AssessmentRecordSource.STATIC_TEST_ONLY if result.runtime_source is JudgeRuntimeSource.STATIC_ONLY else AssessmentRecordSource.FUTURE_JUDGE_RUNTIME, record_version='1.0', input_asset_id=asset.asset_id, runtime_source=result.runtime_source)
        self._writer.append(record, judge_input)
        return record
