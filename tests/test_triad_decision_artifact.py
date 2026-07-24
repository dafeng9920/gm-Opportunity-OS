import ast
import sqlite3
import unittest
from pathlib import Path
from types import MappingProxyType

from governance.triad.contracts import GateDecision, GateDecisionRecord, GovernanceTask, Role, RoleArtifact
from governance.triad.decisions import (
    DecisionArtifactSource,
    GovernanceSnapshotFactory,
    TriadDecisionArtifact,
    TriadDecisionStore,
    TriadDecisionWriter,
)


class TriadDecisionArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"triad-decision-artifact-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.store = TriadDecisionStore(self.database)
        self.writer = TriadDecisionWriter(self.store)
        self.task = GovernanceTask(
            "governance-1", "govern admission", ("assessment-1",), "gate decision",
            metadata=MappingProxyType({"assessment_id": "assessment-1"}), candidate_id="candidate-1",
        )
        self.roles = (
            RoleArtifact("governance-1", Role.EXECUTION, "execution", input_refs=("assessment-1",)),
            RoleArtifact("governance-1", Role.REVIEW, "review", input_refs=("assessment-1",)),
            RoleArtifact("governance-1", Role.COMPLIANCE, "compliance", input_refs=("assessment-1",)),
        )

    def artifact(self, source: DecisionArtifactSource = DecisionArtifactSource.STATIC_TEST_ONLY) -> TriadDecisionArtifact:
        return TriadDecisionArtifact(
            "governance-1", "candidate-1", "assessment-1",
            GateDecisionRecord("governance-1", GateDecision.ALLOW, "validated", Role.COMPLIANCE),
            self.roles, () if source is DecisionArtifactSource.STATIC_TEST_ONLY else ("triad-audit-1",), source, "0.1",
        )

    def test_writer_persists_append_only_validated_runtime_artifact(self) -> None:
        artifact = self.artifact(DecisionArtifactSource.FUTURE_TRIAD_RUNTIME)
        self.writer.append(artifact, self.task)
        self.assertEqual(self.store.get(artifact.decision_artifact_id), artifact)
        self.assertEqual(self.store.list(), [artifact])
        with self.assertRaises(sqlite3.IntegrityError):
            self.writer.append(artifact, self.task)
        self.assertFalse(hasattr(self.store, "update"))
        self.assertFalse(hasattr(self.store, "delete"))

    def test_static_artifact_requires_explicit_test_mode(self) -> None:
        artifact = self.artifact()
        with self.assertRaises(PermissionError):
            self.writer.append(artifact, self.task)
        self.writer.append(artifact, self.task, test_mode=True)
        with self.assertRaises(PermissionError):
            GovernanceSnapshotFactory(self.store).create(artifact.decision_artifact_id)
        snapshot = GovernanceSnapshotFactory(self.store).create(artifact.decision_artifact_id, test_mode=True)
        self.assertEqual(snapshot.decision, GateDecision.ALLOW)
        self.assertEqual(snapshot.decision_artifact_id, artifact.decision_artifact_id)

    def test_writer_rejects_task_lineage_and_incomplete_role_chain(self) -> None:
        artifact = self.artifact(DecisionArtifactSource.FUTURE_TRIAD_RUNTIME)
        wrong_task = GovernanceTask("other", "govern admission", ("assessment-1",), "gate decision", candidate_id="candidate-1")
        with self.assertRaisesRegex(ValueError, "task"):
            self.writer.append(artifact, wrong_task)
        incomplete = TriadDecisionArtifact(
            "governance-1", "candidate-1", "assessment-1", artifact.decision,
            self.roles[:-1], ("triad-audit-1",), DecisionArtifactSource.FUTURE_TRIAD_RUNTIME, "0.1",
        )
        with self.assertRaises(ValueError):
            self.writer.append(incomplete, self.task)

    def test_snapshot_factory_requires_persisted_artifact(self) -> None:
        with self.assertRaises(KeyError):
            GovernanceSnapshotFactory(self.store).create("missing")

    def test_decision_asset_boundary_has_no_runtime_executor_or_packet_assembler_dependency(self) -> None:
        for path in (
            "governance/triad/decisions/contracts.py",
            "governance/triad/decisions/store.py",
            "governance/triad/decisions/writer.py",
        ):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ("runtime", "governance.triad.dispatch", "opportunity.packets", "skills", "adapters", "crawlers"):
                self.assertNotIn(forbidden, imports)