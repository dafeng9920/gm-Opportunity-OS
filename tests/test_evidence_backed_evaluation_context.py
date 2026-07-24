import ast
import unittest
from pathlib import Path

from candidates import CandidateFormationRequest, CandidateFormationService, CandidateRepository, EvidenceReferenceValidator
from core.schemas import CandidatePacket, EvidenceObject
from evidence import EvidenceLedger
from opportunity.evaluation import (
    CandidateEvaluationService,
    EvaluationContext,
    EvaluationFact,
    EvaluationFactCategory,
    EvaluationGateAdapter,
    EvidenceResolver,
    FactVerification,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.gates.contracts import GateStatus


class EvidenceBackedEvaluationTests(unittest.TestCase):
    FACTS = (
        ("trend_up", "DEMAND", True),
        ("keyword_difficulty", "COMPETITION", 20),
        ("long_tail_count", "CONTENT", 12),
        ("available_sources", "DATA", ["official", "community"]),
        ("monetization_path", "MONETIZATION", "ads"),
    )

    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"evaluation-context-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = []
        for fact_id, category, value in self.FACTS:
            item = EvidenceObject(
                "fixture-source", "fact", f"https://example.test/{fact_id}",
                metadata={"evaluation_facts": [{"fact_id": fact_id, "category": category, "value": value, "confidence": 0.8}]},
            )
            self.ledger.append(item)
            self.evidence.append(item)
        self.repository = CandidateRepository(self.database)
        formation = CandidateFormationService(
            EvidenceReferenceValidator(self.ledger), self.repository, ("roblox",)
        )
        self.candidate = formation.form(CandidateFormationRequest(
            "roblox", "Fixture Game", tuple(item.id for item in self.evidence), "human.fixture", "0.1"
        )).candidate_packet
        self.resolver = EvidenceResolver(EvidenceReferenceValidator(self.ledger))
        self.service = CandidateEvaluationService(
            self.repository, self.resolver, OpportunityGateEngine(), ("roblox",)
        )

    def test_resolver_creates_context_with_complete_evidence_lineage(self) -> None:
        context = self.resolver.resolve(self.candidate, "roblox")
        self.assertEqual(context.candidate_id, self.candidate.id)
        self.assertEqual(context.evidence_refs, self.candidate.evidence_ids)
        self.assertEqual({fact.fact_id for fact in context.facts}, {item[0] for item in self.FACTS})
        self.assertTrue(all(len(fact.evidence_ids) == 1 for fact in context.facts))

    def test_resolver_rejects_missing_foreign_and_malformed_evidence_metadata(self) -> None:
        with self.assertRaises(ValueError):
            self.resolver.resolve(self.candidate, "roblox", self.candidate.evidence_ids[:-1])
        foreign = EvidenceObject("foreign", "fact", "https://example.test/foreign")
        self.ledger.append(foreign)
        with self.assertRaises(ValueError):
            self.resolver.resolve(self.candidate, "roblox", self.candidate.evidence_ids + (foreign.id,))
        malformed = EvidenceObject("bad", "fact", "https://example.test/malformed", metadata={"evaluation_facts": "not-a-list"})
        self.ledger.append(malformed)
        bad_candidate = CandidatePacket("Bad", "signal", (malformed.id,), "bad", 0.5)
        with self.assertRaises(ValueError):
            self.resolver.resolve(bad_candidate, "roblox")

    def test_service_runs_candidate_context_gate_and_preserves_field_lineage(self) -> None:
        result = self.service.evaluate(self.candidate.id, "roblox")
        self.assertTrue(all(item.status is GateStatus.PASS for item in result.assessment.results))
        self.assertEqual({field.field for field in result.gate_input.fields}, {item[0] for item in self.FACTS})
        self.assertTrue(all(field.evidence_ids for field in result.gate_input.fields))

    def test_service_rejects_missing_evidence_incomplete_fact_and_unsupported_domain(self) -> None:
        missing = CandidatePacket("Missing", "signal", ("missing-evidence",), "fixture", 0.5)
        self.repository.create(missing)
        with self.assertRaises(KeyError):
            self.service.evaluate(missing.id, "roblox")
        incomplete_evidence = EvidenceObject(
            "fixture", "fact", "https://example.test/incomplete",
            metadata={"evaluation_facts": [{"fact_id": "trend_up", "category": "DEMAND", "value": True}]},
        )
        self.ledger.append(incomplete_evidence)
        incomplete = CandidatePacket("Incomplete", "signal", (incomplete_evidence.id,), "fixture", 0.5)
        self.repository.create(incomplete)
        with self.assertRaisesRegex(ValueError, "missing verified gate facts"):
            self.service.evaluate(incomplete.id, "roblox")
        with self.assertRaises(ValueError):
            self.service.evaluate(self.candidate.id, "unsupported-domain")

    def test_unverified_input_cannot_become_gate_pass_input(self) -> None:
        verified = [
            EvaluationFact("keyword_difficulty", EvaluationFactCategory.COMPETITION, 20, (self.evidence[1].id,), 1.0),
            EvaluationFact("long_tail_count", EvaluationFactCategory.CONTENT, 12, (self.evidence[2].id,), 1.0),
            EvaluationFact("available_sources", EvaluationFactCategory.DATA, ("official", "community"), (self.evidence[3].id,), 1.0),
            EvaluationFact("monetization_path", EvaluationFactCategory.MONETIZATION, "ads", (self.evidence[4].id,), 1.0),
        ]
        unverified = EvaluationFact(
            "trend_up", EvaluationFactCategory.DEMAND, True, (self.evidence[0].id,), 1.0,
            FactVerification.UNVERIFIED_INPUT,
        )
        context = EvaluationContext(self.candidate.id, "roblox", tuple([unverified, *verified]), self.candidate.evidence_ids)
        with self.assertRaisesRegex(ValueError, "missing verified gate facts"):
            EvaluationGateAdapter().to_gate_input(context)

    def test_evaluation_boundary_has_no_judge_triad_packet_consumer_skill_or_runtime_dependencies(self) -> None:
        for path in (
            "opportunity/evaluation/resolver.py",
            "opportunity/evaluation/gate_adapter.py",
            "opportunity/evaluation/service.py",
        ):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in (
                "opportunity.judge", "governance", "opportunity.packets", "opportunity.consumers",
                "skills", "builders", "runtime", "adapters", "crawlers",
            ):
                self.assertNotIn(forbidden, imports)
