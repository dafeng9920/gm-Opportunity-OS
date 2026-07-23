import unittest

from evaluations import ComponentEvaluation


class EvaluationSchemaTests(unittest.TestCase):
    def test_accepts_only_defined_decisions(self) -> None:
        evaluation = ComponentEvaluation("Example", "https://example.test", "1.0", "MIT", "isolated", "none", "none", "none", "none", "ADAPT")
        self.assertEqual(evaluation.decision, "ADAPT")
        with self.assertRaises(ValueError):
            ComponentEvaluation("Example", "https://example.test", "1.0", "MIT", "isolated", "none", "none", "none", "none", "PENDING")  # type: ignore[arg-type]
