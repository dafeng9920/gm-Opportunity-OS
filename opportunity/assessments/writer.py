"""Controlled writer for Assessment assets; future Runtime remains the production owner."""

from __future__ import annotations

from opportunity.judge.contracts import JudgeInput

from .contracts import AssessmentRecordSource, JudgeAssessmentRecord, JudgeAssessmentRecordValidator
from .store import JudgeAssessmentStore


class AssessmentRecordWriter:
    """Writes only declared provenance sources after JudgeInput lineage validation."""

    def __init__(self, store: JudgeAssessmentStore, validator: JudgeAssessmentRecordValidator | None = None) -> None:
        self._store = store
        self._validator = validator or JudgeAssessmentRecordValidator()

    def append(self, record: JudgeAssessmentRecord, judge_input: JudgeInput) -> None:
        if record.source not in {
            AssessmentRecordSource.FUTURE_JUDGE_RUNTIME,
            AssessmentRecordSource.STATIC_TEST_ONLY,
        }:
            raise PermissionError("assessment record source is not permitted")
        self._validator.validate(record, judge_input)
        self._store.append(record)
