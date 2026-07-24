import ast
import unittest
from pathlib import Path

from candidates import CandidateFormationRequest, CandidateFormationService, CandidateRepository, EvidenceReferenceValidator
from core.schemas import EvidenceObject
from evidence import EvidenceLedger
from opportunity.evaluation import CandidateEvaluationService, EvidenceResolver, FactVerification
from opportunity.gates import OpportunityGateEngine
from opportunity.judge import JudgeInputAssembler
from tests.fact_test_support import produce_all


class JudgeInputAssemblyTests(unittest.TestCase):
    FACTS = (
        ("trend_up", "DEMAND", True),
        ("keyword_difficulty", "COMPETITION", 20),
        ("long_tail_count", "CONTENT", 12),
        ("available_sources", "DATA", ["official", "community"]),
        ("monetization_path", "MONETIZATION", "ads"),
    )

    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"judge-input-assembly-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = []
        for fact_id, category, value in self.FACTS:
            references = tuple(item.id for item in self.evidence[:2]) if fact_id == "available_sources" else None
            item = EvidenceObject(
                "fixture", "fact", f"https://example.test/{fact_id}",
                metadata={"evaluation_facts": [self._fact(fact_id, category, value, references)]},
            )
            self.ledger.append(item)
            self.evidence.append(item)
        self.fact_store = produce_all(self.ledger, self.database, self.evidence)
        self.repository = CandidateRepository(self.database)
        formation = CandidateFormationService(EvidenceReferenceValidator(self.ledger), self.repository, ("roblox",))
        self.candidate = formation.form(CandidateFormationRequest(
            "roblox", "Fixture Game", tuple(item.id for item in self.evidence), "human.fixture", "0.1"
        )).candidate_packet
        self.result = self._fresh_result()
        self.assembler = JudgeInputAssembler(self.repository, EvidenceReferenceValidator(self.ledger))

    @staticmethod
    def _provenance(fact_id: str) -> dict[str, str]:
        return {
            "trend_up": {"query": "fixture", "region": "US", "time_window": "7d", "source": "fixture", "method": "fixture-v1", "captured_at": "2026-01-01"},
            "keyword_difficulty": {"query": "fixture", "source": "fixture", "method": "fixture-v1", "captured_at": "2026-01-01"},
            "long_tail_count": {"query_family": "fixture", "source": "fixture", "method": "fixture-v1", "captured_at": "2026-01-01"},
            "available_sources": {"source_inventory": "fixture", "method": "fixture-v1", "captured_at": "2026-01-01"},
            "monetization_path": {"path_scope": "site", "source": "fixture", "method": "fixture-v1", "captured_at": "2026-01-01"},
        }[fact_id]

    def _fact(self, fact_id: str, category: str, value: object, references: tuple[str, ...] | None) -> dict[str, object]:
        fact: dict[str, object] = {"fact_id": fact_id, "category": category, "value": value, "fact_version": "0.1", "provenance": self._provenance(fact_id)}
        if references:
            fact["evidence_ids"] = references
        return fact

    def test_evaluation_result_assembles_validated_judge_input(self) -> None:
        packet = self.assembler.assemble(self.result)
        self.assertEqual(packet.candidate.id, self.candidate.id)
        self.assertEqual({item.id for item in packet.evidence}, set(self.candidate.evidence_ids))
        self.assertEqual(packet.gate_results, self.result.assessment.results)

    def test_assembler_rejects_candidate_mismatch_and_missing_context(self) -> None:
        object.__setattr__(self.result, "candidate_id", "other-candidate")
        with self.assertRaisesRegex(ValueError, "candidate"):
            self.assembler.assemble(self.result)
        self.result = self._fresh_result()
        object.__setattr__(self.result, "context", None)
        with self.assertRaisesRegex(ValueError, "evaluation context"):
            self.assembler.assemble(self.result)

    def test_assembler_rejects_foreign_context_evidence_and_gate_evidence(self) -> None:
        object.__setattr__(self.result.context, "evidence_refs", ("foreign-evidence",))
        with self.assertRaisesRegex(ValueError, "candidate evidence"):
            self.assembler.assemble(self.result)
        self.result = self._fresh_result()
        object.__setattr__(self.result.assessment.results[0], "evidence_refs", ("foreign-evidence",))
        with self.assertRaisesRegex(ValueError, "gate result evidence"):
            self.assembler.assemble(self.result)

    def test_assembler_rejects_unverified_evaluation_fact(self) -> None:
        object.__setattr__(self.result.context.facts[0], "verification", FactVerification.UNVERIFIED_INPUT)
        with self.assertRaisesRegex(ValueError, "unverified"):
            self.assembler.assemble(self.result)

    def test_assembler_rejects_gate_field_lineage_mismatch(self) -> None:
        field = self.result.gate_input.fields[0]
        object.__setattr__(field, "evidence_ids", ("foreign-evidence",))
        with self.assertRaisesRegex(ValueError, "gate input field"):
            self.assembler.assemble(self.result)

    def test_assembler_has_no_judge_runner_agent_runtime_triad_packet_consumer_or_builder_dependencies(self) -> None:
        tree = ast.parse(Path("opportunity/judge/assembler.py").read_text(encoding="utf-8-sig"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("opportunity.judge.runner", "runtime", "skills", "governance", "opportunity.packets", "opportunity.consumers", "builders", "adapters", "crawlers"):
            self.assertNotIn(forbidden, imports)

    def _fresh_result(self):
        return CandidateEvaluationService(
            self.repository,
            EvidenceResolver(EvidenceReferenceValidator(self.ledger), self.fact_store),
            OpportunityGateEngine(),
            ("roblox",),
        ).evaluate(self.candidate.id, "roblox")