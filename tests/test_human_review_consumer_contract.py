import ast
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from opportunity.consumers import ConsumerCapability, ConsumerIdentity, ConsumerRegistry, ConsumerType, PacketReference
from opportunity.consumers.contracts import ConsumerAction
from opportunity.human_review import (
    HumanReviewDecision,
    HumanReviewDecisionType,
    HumanReviewRequest,
    HumanReviewValidator,
)


class HumanReviewConsumerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = Path(".opportunity-os") / f"human-review-{self._testMethodName}.db"
        if self.db.exists():
            self.db.unlink()
        self.registry = ConsumerRegistry(self.db)
        self.registry.register(
            ConsumerIdentity("human.reviewer", ConsumerType.HUMAN, "0.1"),
            ConsumerCapability("human.reviewer", (ConsumerAction.READ,), ("0.1",), "review packet", "0.1"),
        )
        self.validator = HumanReviewValidator(self.registry)

    def request(self, consumer_id: str = "human.reviewer", packet_version: str = "0.1") -> HumanReviewRequest:
        return HumanReviewRequest(consumer_id, PacketReference("packet-1", packet_version), packet_version)

    def decision(self, request: HumanReviewRequest, kind: HumanReviewDecisionType = HumanReviewDecisionType.APPROVE) -> HumanReviewDecision:
        return HumanReviewDecision(request.review_id, kind, request.consumer_id, "Evidence and gate results reviewed.")

    def test_valid_human_review_request(self) -> None:
        request = self.request()
        self.validator.validate_request(request, "0.1")
        self.assertEqual(request.packet_reference.packet_id, "packet-1")

    def test_request_rejects_non_human_consumer_and_invalid_packet_reference(self) -> None:
        self.registry.register(
            ConsumerIdentity("service.reader", ConsumerType.SERVICE, "0.1"),
            ConsumerCapability("service.reader", (ConsumerAction.READ,), ("0.1",), "read packet", "0.1"),
        )
        with self.assertRaises(PermissionError):
            self.validator.validate_request(self.request("service.reader"), "0.1")
        with self.assertRaises(ValueError):
            PacketReference("", "0.1")
        with self.assertRaises(ValueError):
            self.validator.validate_request(HumanReviewRequest("human.reviewer", PacketReference("packet-1", "0.1"), "0.2"), "0.1")

    def test_all_allowed_human_review_decisions_and_invalid_decision(self) -> None:
        request = self.request()
        for kind in HumanReviewDecisionType:
            self.assertEqual(self.decision(request, kind).decision, kind)
        with self.assertRaises(ValueError):
            HumanReviewDecision(request.review_id, "ESCALATE", request.consumer_id, "reason")
        with self.assertRaises(ValueError):
            HumanReviewDecision(request.review_id, HumanReviewDecisionType.REJECT, request.consumer_id, " ")

    def test_record_creation_and_immutable_behavior(self) -> None:
        request = self.request()
        self.validator.validate_request(request, "0.1")
        record = self.validator.create_record(request, self.decision(request, HumanReviewDecisionType.REQUEST_MORE_EVIDENCE))
        self.assertEqual(record.decision, HumanReviewDecisionType.REQUEST_MORE_EVIDENCE)
        with self.assertRaises(FrozenInstanceError):
            record.reason = "changed"  # type: ignore[misc]

    def test_decision_must_match_review_and_requested_human(self) -> None:
        request = self.request()
        with self.assertRaises(ValueError):
            self.validator.create_record(request, HumanReviewDecision("other-review", HumanReviewDecisionType.APPROVE, request.consumer_id, "reason"))
        with self.assertRaises(PermissionError):
            self.validator.create_record(request, HumanReviewDecision(request.review_id, HumanReviewDecisionType.APPROVE, "another.human", "reason"))

    def test_human_review_layer_is_independent_of_decision_and_runtime_layers(self) -> None:
        for path in ("opportunity/human_review/contracts.py", "opportunity/human_review/validator.py"):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ("opportunity.gates", "opportunity.judge", "governance", "runtime", "skills", "builders", "evidence", "candidates"):
                self.assertNotIn(forbidden, imports)
