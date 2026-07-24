import unittest

from opportunity.evaluation import (
    DEFAULT_GATE_FACT_REGISTRY,
    EvaluationFact,
    EvaluationFactCategory,
    FactVerification,
    GateFactValidator,
)


class GateFactContractTests(unittest.TestCase):
    def _fact(self, fact_id: str, category: EvaluationFactCategory, value, evidence_ids: tuple[str, ...], provenance: dict[str, object], version: str = "0.1") -> EvaluationFact:
        return EvaluationFact(fact_id, category, value, evidence_ids, 0.8, FactVerification.EVIDENCE_BACKED, version, provenance)

    def test_registry_defines_the_five_versioned_gate_facts(self) -> None:
        definitions = {item.fact_id: item for item in DEFAULT_GATE_FACT_REGISTRY.list()}
        self.assertEqual(set(definitions), {"trend_up", "keyword_difficulty", "long_tail_count", "available_sources", "monetization_path"})
        self.assertEqual(definitions["trend_up"].version, "0.1")
        self.assertEqual(definitions["available_sources"].evidence_semantics.value, "MULTI")

    def test_trend_requires_boolean_value_and_complete_provenance(self) -> None:
        valid = self._fact(
            "trend_up", EvaluationFactCategory.DEMAND, True, ("evidence-1",),
            {"query": "grow a garden", "region": "US", "time_window": "30d", "source": "trend-source", "method": "delta-v1", "captured_at": "2026-01-01"},
        )
        GateFactValidator().validate(valid)
        with self.assertRaisesRegex(ValueError, "value"):
            self._fact("trend_up", EvaluationFactCategory.DEMAND, "yes", ("evidence-1",), dict(valid.provenance))
        with self.assertRaisesRegex(ValueError, "provenance"):
            self._fact("trend_up", EvaluationFactCategory.DEMAND, True, ("evidence-1",), {"query": "x"})

    def test_available_sources_requires_multiple_evidence_references(self) -> None:
        provenance = {"source_inventory": "official-and-community", "method": "inventory-v1", "captured_at": "2026-01-01"}
        with self.assertRaisesRegex(ValueError, "multiple"):
            self._fact("available_sources", EvaluationFactCategory.DATA, ("official", "community"), ("evidence-1",), provenance)
        valid = self._fact("available_sources", EvaluationFactCategory.DATA, ("official", "community"), ("evidence-1", "evidence-2"), provenance)
        GateFactValidator().validate(valid)

    def test_unknown_fact_version_cannot_become_a_gate_fact(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown gate fact version"):
            self._fact(
                "keyword_difficulty", EvaluationFactCategory.COMPETITION, 20, ("evidence-1",),
                {"query": "grow a garden", "source": "serp", "method": "kd-v2", "captured_at": "2026-01-01"},
                "9.9",
            )

    def test_unverified_input_is_not_promoted_by_construction(self) -> None:
        fact = EvaluationFact("trend_up", EvaluationFactCategory.DEMAND, True, ("evidence-1",), 0.8, FactVerification.UNVERIFIED_INPUT)
        self.assertIs(fact.verification, FactVerification.UNVERIFIED_INPUT)