import unittest

from core.schemas import CandidatePacket, Component, EvidenceObject


class SchemaTests(unittest.TestCase):
    def test_evidence_derives_hash_from_raw_reference(self) -> None:
        evidence = EvidenceObject(source="manual", source_type="url", raw_reference="https://example.test/signal")
        self.assertEqual(len(evidence.content_hash), 64)

    def test_evidence_rejects_tampered_hash(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceObject(source="manual", source_type="url", raw_reference="x", content_hash="tampered")

    def test_candidate_requires_evidence_and_bounded_confidence(self) -> None:
        with self.assertRaises(ValueError):
            CandidatePacket(title="x", signal="x", evidence_ids=(), source="x", confidence=0.5)
        with self.assertRaises(ValueError):
            CandidatePacket(title="x", signal="x", evidence_ids=("e1",), source="x", confidence=1.1)

    def test_component_validates_type(self) -> None:
        with self.assertRaises(ValueError):
            Component(id="x", name="x", type="unknown", version="0.1", status="active", capability="x")  # type: ignore[arg-type]
