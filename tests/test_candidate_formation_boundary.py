import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

from candidates import (
    CandidateFormationRequest,
    CandidateFormationService,
    CandidateRepository,
    EvidenceReferenceValidator,
)
from core.schemas import EvidenceObject
from evidence import EvidenceLedger


class EvidenceReferenceValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"candidate-formation-validator-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject("youtube", "signal", "https://example.test/video")
        self.ledger.append(self.evidence)
        self.validator = EvidenceReferenceValidator(self.ledger)

    def test_valid_and_missing_evidence_ids(self) -> None:
        self.assertEqual(self.validator.validate((self.evidence.id,)), (self.evidence,))
        with self.assertRaises(KeyError):
            self.validator.validate(("missing-evidence",))
        with self.assertRaises(ValueError):
            self.validator.validate(("",))

    def test_validator_rejects_missing_source_or_timestamp(self) -> None:
        class Lookup:
            def __init__(self, evidence):
                self.evidence = evidence
            def get(self, evidence_id):
                return self.evidence
        with self.assertRaisesRegex(ValueError, "source"):
            EvidenceReferenceValidator(Lookup(SimpleNamespace(source="", captured_time="time", content_hash="hash"))).validate(("evidence-1",))
        with self.assertRaisesRegex(ValueError, "captured_time"):
            EvidenceReferenceValidator(Lookup(SimpleNamespace(source="source", captured_time="", content_hash="hash"))).validate(("evidence-1",))


class CandidateFormationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"candidate-formation-service-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        self.ledger = EvidenceLedger(self.database)
        self.evidence = EvidenceObject("youtube", "signal", "https://example.test/roblox-video")
        self.ledger.append(self.evidence)
        self.repository = CandidateRepository(self.database)
        self.service = CandidateFormationService(
            EvidenceReferenceValidator(self.ledger), self.repository, ("roblox",)
        )

    def request(self, domain: str = "roblox", evidence_ids: tuple[str, ...] | None = None) -> CandidateFormationRequest:
        return CandidateFormationRequest(
            domain, "Fixture Roblox Game", evidence_ids if evidence_ids is not None else (self.evidence.id,),
            "human.fixture", "0.1", confidence=0.5,
        )

    def test_evidence_becomes_persisted_candidate_with_exact_lineage(self) -> None:
        result = self.service.form(self.request())
        persisted = self.repository.get(result.candidate_id)
        self.assertTrue(result.evidence_verified)
        self.assertEqual(result.candidate_packet.evidence_ids, (self.evidence.id,))
        self.assertEqual(persisted.evidence_ids, (self.evidence.id,))
        self.assertEqual(result.candidate_packet.status, "CANDIDATE_CREATED")

    def test_empty_invalid_reference_and_unsupported_domain_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CandidateFormationRequest("roblox", "Fixture", (), "human.fixture", "0.1")
        with self.assertRaises(ValueError):
            CandidateFormationRequest("roblox", "Fixture", [self.evidence.id], "human.fixture", "0.1")  # type: ignore[arg-type]
        with self.assertRaises(KeyError):
            self.service.form(self.request(evidence_ids=("missing-evidence",)))
        with self.assertRaises(ValueError):
            self.service.form(self.request(domain="unsupported-domain"))

    def test_candidate_formation_has_no_decision_or_runtime_dependencies(self) -> None:
        for path in ("candidates/evidence_validator.py", "candidates/formation_service.py"):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in (
                "opportunity.gates", "opportunity.judge", "governance", "skills", "builders",
                "runtime", "opportunity.packets", "opportunity.consumers",
            ):
                self.assertNotIn(forbidden, imports)
