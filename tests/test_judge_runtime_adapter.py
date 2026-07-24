import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from opportunity.assessments import AssessmentRecordWriter, JudgeAssessmentStore, JudgeRuntimeSource
from opportunity.judge import JudgeRuntimeAdapter, JudgeRuntimeResult, StaticJudgeAssessmentRuntime
from tests.test_judge_boundary_foundation import JudgeBoundaryFoundationTests


class JudgeRuntimeAdapterTests(JudgeBoundaryFoundationTests):
    # Reuse only the fixture builder; inherited Phase 18.13 tests run in their own module.
    test_bridge_and_static_runtime_have_no_llm_agent_or_triad_dependencies = None
    test_gate_assessment_becomes_scoped_judge_input_and_static_asset = None
    test_out_of_scope_fact_reference_is_rejected = None
    test_produced_fact_cannot_enter_judge_scope = None
    test_runtime_gate_record_cannot_bypass_persisted_asset = None
    def adapter(self, runtime=None):
        store = JudgeAssessmentStore(self.database)
        return JudgeRuntimeAdapter(self.assembler, AssessmentRecordWriter(store), runtime or StaticJudgeAssessmentRuntime()), store

    def test_static_runtime_adapter_persists_provenance_bound_record(self):
        adapter, store = self.adapter()
        record = adapter.assess(self.asset)
        self.assertEqual(record.input_asset_id, self.asset.asset_id)
        self.assertEqual(record.runtime_source, JudgeRuntimeSource.STATIC_ONLY)
        self.assertEqual(store.get(record.assessment_id), record)

    def test_invalid_runtime_output_is_rejected_before_write(self):
        class Invalid(StaticJudgeAssessmentRuntime):
            def execute(self, invocation): return {'new_fact': 'forbidden'}
        adapter, store = self.adapter(Invalid())
        with self.assertRaisesRegex(TypeError, 'JudgeRuntimeResult'):
            adapter.assess(self.asset)
        self.assertEqual(store.list(), [])

    def test_declared_runtime_source_mismatch_is_rejected(self):
        class Mismatch(StaticJudgeAssessmentRuntime):
            def execute(self, invocation):
                result = super().execute(invocation)
                return JudgeRuntimeResult(result.decision, result.assessment, result.reasoning_reference, JudgeRuntimeSource.LLM_RUNTIME, result.runtime_id, result.runtime_version)
        adapter, store = self.adapter(Mismatch())
        with self.assertRaisesRegex(ValueError, 'source declaration mismatch'):
            adapter.assess(self.asset)
        self.assertEqual(store.list(), [])

    def test_runtime_cannot_modify_immutable_asset(self):
        with self.assertRaises(FrozenInstanceError):
            self.asset.candidate_id = 'other'  # type: ignore[misc]


# Do not expose the imported fixture class as a second unittest target in this module.
JudgeBoundaryFoundationTests = None
