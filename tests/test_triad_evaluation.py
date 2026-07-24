"""Unit tests for the Triad Evaluation foundation (Phase 18.16).

Covers the assembler status logic, scope/role validation, the asset-bound
judge-record guard, append-only storage, and a static import boundary.
"""

from __future__ import annotations

import ast
import sqlite3
import unittest
from pathlib import Path
from typing import Iterable

from opportunity.assessments import (
    AssessmentRecordSource,
    JudgeAssessmentRecord,
    JudgeRuntimeSource,
)
from opportunity.judge.contracts import AssessmentRecommendation, JudgeAssessment
from opportunity.triad_evaluation import (
    RoleAssessmentRecord,
    RoleAssessmentStore,
    TriadContextStatus,
    TriadEvaluationAssembler,
    TriadRoleContract,
)


def _role(role_id: str) -> TriadRoleContract:
    return TriadRoleContract(
        role_id,
        role_id,
        ("GateAssessmentAsset",),
        ("GateAssessmentAsset",),
        ("RawEvidenceWrite",),
        "RoleAssessmentRecord",
        "0.1",
    )


def _role_assessment(role_id: str, input_asset_id: str = "asset-1") -> RoleAssessmentRecord:
    return RoleAssessmentRecord(
        f"{role_id}-assessment",
        role_id,
        input_asset_id,
        f"judge-{role_id}",
        JudgeRuntimeSource.STATIC_ONLY,
        AssessmentRecommendation.SMALL_SCALE_VALIDATION.value,
        ("input-hash",),
        "0.1",
    )


def _judge_record(*, input_asset_id: str = "LEGACY_UNBOUND") -> JudgeAssessmentRecord:
    assessment = JudgeAssessment(
        "candidate-1",
        "fixture explanation",
        (),  # risks
        AssessmentRecommendation.SMALL_SCALE_VALIDATION,
        ("evidence-1",),
        ("demand@0.1",),
    )
    return JudgeAssessmentRecord(
        judge_input_hash="a" * 64,
        candidate_id="candidate-1",
        assessment=assessment,
        evidence_refs=("evidence-1",),
        gate_refs=("demand@0.1",),
        skill_id="opportunity.judge",
        skill_version="v0.1",
        runtime_id="STATIC_ONLY",
        runtime_version="STATIC_ONLY",
        audit_refs=("audit-1",),
        source=AssessmentRecordSource.STATIC_TEST_ONLY,
        record_version="1.0",
        input_asset_id=input_asset_id,
    )


class TriadEvaluationAssemblerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.roles = tuple(_role(role_id) for role_id in ("discovery", "skeptic", "commercial"))
        self.assembler = TriadEvaluationAssembler()

    def test_full_roles_produce_ready_context(self) -> None:
        context = self.assembler.assemble(
            "candidate-1",
            "asset-1",
            self.roles,
            tuple(_role_assessment(role.role_id) for role in self.roles),
        )
        self.assertIs(context.status, TriadContextStatus.READY)
        self.assertEqual(set(context.required_roles), {"discovery", "skeptic", "commercial"})
        self.assertEqual(len(context.role_assessments), 3)

    def test_missing_role_produces_unknown_context(self) -> None:
        context = self.assembler.assemble(
            "candidate-1",
            "asset-1",
            self.roles,
            (_role_assessment("discovery"), _role_assessment("skeptic")),
        )
        self.assertIs(context.status, TriadContextStatus.UNKNOWN)

    def test_duplicate_required_roles_are_rejected(self) -> None:
        duplicated = (_role("discovery"), _role("discovery"), _role("skeptic"))
        with self.assertRaisesRegex(ValueError, "required roles must be unique"):
            self.assembler.assemble(
                "candidate-1",
                "asset-1",
                duplicated,
                (_role_assessment("discovery"), _role_assessment("skeptic")),
            )

    def test_role_assessment_with_unknown_role_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "role assessment scope mismatch"):
            self.assembler.assemble(
                "candidate-1",
                "asset-1",
                self.roles,
                (_role_assessment("discovery"), _role_assessment("foreign")),
            )

    def test_role_assessment_with_foreign_input_asset_is_rejected(self) -> None:
        foreign = RoleAssessmentRecord(
            "foreign-assessment",
            "discovery",
            "other-asset",  # different input_asset_id
            "judge-discovery",
            JudgeRuntimeSource.STATIC_ONLY,
            AssessmentRecommendation.SMALL_SCALE_VALIDATION.value,
            ("input-hash",),
            "0.1",
        )
        with self.assertRaisesRegex(ValueError, "role assessment scope mismatch"):
            self.assembler.assemble("candidate-1", "asset-1", self.roles, (foreign,))

    def test_role_record_rejects_legacy_unbound_judge(self) -> None:
        # Default JudgeAssessmentRecord is not asset-bound.
        with self.assertRaisesRegex(ValueError, "asset-bound"):
            self.assembler.role_record(_role("discovery"), _judge_record())

    def test_role_record_binds_asset_bound_judge_provenance(self) -> None:
        record = _judge_record(input_asset_id="asset-1")
        role_assessment = self.assembler.role_record(_role("discovery"), record)
        self.assertEqual(role_assessment.role_id, "discovery")
        self.assertEqual(role_assessment.input_asset_id, "asset-1")
        self.assertEqual(role_assessment.judge_assessment_id, record.assessment_id)
        self.assertIs(role_assessment.runtime_source, record.runtime_source)
        self.assertEqual(role_assessment.assessment_result, record.assessment.recommendation.value)
        self.assertEqual(role_assessment.provenance, (record.judge_input_hash,))
        self.assertEqual(role_assessment.version, "0.1")


class RoleAssessmentStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"triad-evaluation-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.store = RoleAssessmentStore(self.database)

    def test_append_get_list_roundtrip_and_idempotent_identity(self) -> None:
        record = _role_assessment("discovery")
        self.store.append(record)
        self.assertEqual(self.store.get(record.role_assessment_id), record)
        self.assertEqual(self.store.list(), [record])
        # append-only: re-inserting the same primary key is rejected by SQLite.
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.append(record)

    def test_store_exposes_no_mutation_methods(self) -> None:
        for mutation in ("update", "delete", "remove", "drop"):
            self.assertFalse(
                hasattr(self.store, mutation),
                f"RoleAssessmentStore must not expose {mutation} (append-only)",
            )


class TriadEvaluationImportBoundaryTests(unittest.TestCase):
    """No LLM / agent / openai dependency in the triad evaluation foundation."""

    @staticmethod
    def _import_modules(paths: Iterable[str]) -> list[str]:
        modules: list[str] = []
        for path in paths:
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    modules.append(node.module or "")
                elif isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
        return modules

    def test_no_llm_or_agent_dependency(self) -> None:
        modules = self._import_modules(
            (
                "opportunity/triad_evaluation/contracts.py",
                "opportunity/triad_evaluation/assembler.py",
                "opportunity/triad_evaluation/store.py",
            )
        )
        for forbidden in ("agents", "openai", "llm", "anthropic"):
            for module in modules:
                self.assertNotIn(forbidden, module)


if __name__ == "__main__":
    unittest.main()
