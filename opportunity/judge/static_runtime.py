"""Static-only Judge boundary for contract and lineage verification; not a real Agent runtime."""
from __future__ import annotations

from opportunity.assessments import (
    AssessmentRecordSource,
    AssessmentRecordWriter,
    JudgeAssessmentRecord,
    JudgeInputHasher,
)

from .contracts import JudgeInput
from .mock_agent import DeterministicJudgeAgent
from .runner import OpportunityJudgeRunner


class StaticJudgeAssessmentRuntime:
    """Persist a deterministic mock assessment with explicit STATIC_ONLY provenance."""

    skill_id = "opportunity.judge"
    skill_version = "v0.1"
    runtime_id = "STATIC_ONLY"
    runtime_version = "STATIC_ONLY"
    record_version = "1.0"

    def __init__(self, writer: AssessmentRecordWriter) -> None:
        self._writer = writer
        self._runner = OpportunityJudgeRunner()
        self._judge = DeterministicJudgeAgent()

    def assess(self, judge_input: JudgeInput) -> JudgeAssessmentRecord:
        assessment = self._runner.assess(self._judge, judge_input)
        record = JudgeAssessmentRecord(
            JudgeInputHasher.hash(judge_input),
            judge_input.candidate.id,
            assessment,
            tuple(item.id for item in judge_input.evidence),
            tuple(f"{item.gate}@{item.version}" for item in judge_input.gate_results),
            self.skill_id,
            self.skill_version,
            self.runtime_id,
            self.runtime_version,
            (),
            AssessmentRecordSource.STATIC_TEST_ONLY,
            self.record_version,
        )
        self._writer.append(record, judge_input)
        return record