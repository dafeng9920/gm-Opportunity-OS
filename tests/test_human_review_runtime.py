import ast
import unittest
from pathlib import Path

from core.schemas import CandidatePacket, EvidenceObject
from governance.triad.contracts import GateDecision
from opportunity.consumers import (
    ConsumerAccessRuntime,
    ConsumerAction,
    ConsumerAuditStore,
    ConsumerCapability,
    ConsumerIdentity,
    ConsumerPolicy,
    ConsumerPolicyGate,
    ConsumerRegistry,
    ConsumerType,
    ConsumerValidator,
    OpportunityPacketReader,
    PacketReference,
)
from opportunity.gates import OpportunityGateEngine
from opportunity.human_review import (
    HumanReviewAuditAction,
    HumanReviewAuditStore,
    HumanReviewDecision,
    HumanReviewDecisionType,
    HumanReviewRequest,
    HumanReviewRuntime,
    HumanReviewSession,
    HumanReviewSessionStatus,
    HumanReviewStore,
    HumanReviewValidator,
)
from opportunity.judge import DeterministicJudgeAgent, JudgeInput, OpportunityJudgeRunner
from opportunity.packets.contracts import OpportunityPacketAssembler
from opportunity.packets.models import GovernanceSnapshot
from opportunity.packets.store import OpportunityPacketStore


class HumanReviewRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = Path(".opportunity-os") / f"human-review-runtime-{self._testMethodName}.db"
        if self.database.exists():
            self.database.unlink()
        evidence = EvidenceObject("test", "signal", "https://example.test/review-source")
        self.candidate = CandidatePacket("Review Example", "signal", (evidence.id,), "test", 0.5)
        gates = OpportunityGateEngine().assess(
            self.candidate,
            {
                "trend_up": True,
                "keyword_difficulty": 20,
                "long_tail_count": 20,
                "available_sources": ("official", "community"),
                "monetization_path": "ads",
            },
        ).results
        judge = OpportunityJudgeRunner().assess(
            DeterministicJudgeAgent(), JudgeInput(self.candidate, (evidence,), gates)
        )
        self.packet = OpportunityPacketAssembler().assemble(
            domain="test-domain",
            candidate=self.candidate,
            evidence=(evidence,),
            gates=gates,
            judge=judge,
            governance=GovernanceSnapshot("REVIEWED", GateDecision.ALLOW, ("audit-1",), "decision-fixture", self.candidate.id, "assessment-fixture"),
            signals=("signal-1",),
            sources=("test",),
            discovery_time=evidence.captured_time,
        )
        packet_store = OpportunityPacketStore(self.database)
        packet_store.create(self.packet)
        self.registry = ConsumerRegistry(self.database)
        self.registry.register(
            ConsumerIdentity("human.reviewer", ConsumerType.HUMAN, "0.1"),
            ConsumerCapability("human.reviewer", (ConsumerAction.READ,), ("0.1",), "review packet", "0.1"),
        )
        self.consumer_audit = ConsumerAuditStore(self.database)
        self.review_store = HumanReviewStore(self.database)
        self.review_audit = HumanReviewAuditStore(self.database)
        self.validator = HumanReviewValidator(self.registry)
        self.reader = OpportunityPacketReader(ConsumerValidator(self.registry), packet_store)

    def runtime(self, policy: ConsumerPolicy | None = None) -> HumanReviewRuntime:
        policy = policy or ConsumerPolicy(
            "policy.human-read", "HUMAN", (ConsumerAction.READ,), ("0.1",), "0.1"
        )
        access = ConsumerAccessRuntime(ConsumerPolicyGate(self.registry, policy), self.consumer_audit)
        return HumanReviewRuntime(self.validator, access, self.reader, self.review_store, self.review_audit)

    def request(self) -> HumanReviewRequest:
        return HumanReviewRequest("human.reviewer", PacketReference(self.packet.opportunity_id, "0.1"), "0.1")

    def decision(self, request: HumanReviewRequest, kind: HumanReviewDecisionType = HumanReviewDecisionType.APPROVE) -> HumanReviewDecision:
        return HumanReviewDecision(request.review_id, kind, "human.reviewer", "Human review completed.")

    def test_session_create_rejects_invalid_reference_and_invalid_transition(self) -> None:
        request = self.request()
        session, snapshot = self.runtime().start_review(request, "0.1")
        self.assertIn(self.packet.opportunity_id, snapshot.serialized_packet)
        self.assertEqual(self.review_store.get_session(session.session_id).status, HumanReviewSessionStatus.OPEN)
        with self.assertRaises(ValueError):
            HumanReviewRequest("human.reviewer", PacketReference("", "0.1"), "0.1")
        with self.assertRaises(ValueError):
            self.review_store.close_session(session.session_id)
        with self.assertRaises(ValueError):
            self.review_store.create_session(
                HumanReviewSession(request.review_id, request.consumer_id, request.packet_reference, "0.1", HumanReviewSessionStatus.SUBMITTED)
            )

    def test_successful_runtime_flow_persists_record_session_history_and_audit(self) -> None:
        request = self.request()
        session, _ = self.runtime().start_review(request, "0.1")
        record = self.runtime().submit_decision(session.session_id, self.decision(request), "0.1")
        self.assertEqual(self.review_store.list_reviews(), [record])
        self.assertEqual(self.review_store.get_session(session.session_id).status, HumanReviewSessionStatus.CLOSED)
        self.assertEqual(
            [event.status for event in self.review_store.list_session_events(session.session_id)],
            [HumanReviewSessionStatus.OPEN, HumanReviewSessionStatus.SUBMITTED, HumanReviewSessionStatus.CLOSED],
        )
        self.assertEqual(
            [event.action for event in self.review_audit.list()],
            [
                HumanReviewAuditAction.ACCESS_REQUESTED,
                HumanReviewAuditAction.PACKET_READ,
                HumanReviewAuditAction.SESSION_CREATED,
                HumanReviewAuditAction.DECISION_SUBMITTED,
                HumanReviewAuditAction.SESSION_CLOSED,
            ],
        )
        self.assertEqual(len(self.consumer_audit.list()), 1)

    def test_policy_deny_creates_access_audit_but_no_session(self) -> None:
        denied = ConsumerPolicy("policy.human-deny", "HUMAN", (), ("0.1",), "0.1")
        with self.assertRaises(PermissionError):
            self.runtime(denied).start_review(self.request(), "0.1")
        self.assertEqual(self.review_audit.list()[0].decision, "DENY")
        self.assertEqual(self.review_store.list_reviews(), [])
        self.assertEqual(len(self.consumer_audit.list()), 1)

    def test_invalid_decision_and_duplicate_submit_are_rejected(self) -> None:
        request = self.request()
        session, _ = self.runtime().start_review(request, "0.1")
        with self.assertRaises(ValueError):
            self.runtime().submit_decision(
                session.session_id,
                HumanReviewDecision("wrong-review", HumanReviewDecisionType.REJECT, "human.reviewer", "reason"),
                "0.1",
            )
        record = self.runtime().submit_decision(session.session_id, self.decision(request, HumanReviewDecisionType.REQUEST_MORE_EVIDENCE), "0.1")
        self.assertEqual(record.decision, HumanReviewDecisionType.REQUEST_MORE_EVIDENCE)
        with self.assertRaises(ValueError):
            self.runtime().submit_decision(session.session_id, self.decision(request), "0.1")

    def test_non_human_consumer_is_rejected_before_policy_access(self) -> None:
        self.registry.register(
            ConsumerIdentity("service.reader", ConsumerType.SERVICE, "0.1"),
            ConsumerCapability("service.reader", (ConsumerAction.READ,), ("0.1",), "read packet", "0.1"),
        )
        request = HumanReviewRequest("service.reader", PacketReference(self.packet.opportunity_id, "0.1"), "0.1")
        with self.assertRaises(PermissionError):
            self.runtime().start_review(request, "0.1")
        self.assertEqual(self.consumer_audit.list(), [])

    def test_runtime_has_no_gate_judge_triad_skill_builder_or_runtime_policy_dependencies(self) -> None:
        for path in (
            "opportunity/human_review/runtime.py",
            "opportunity/human_review/store.py",
            "opportunity/human_review/audit_store.py",
        ):
            tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
            imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            for forbidden in ("opportunity.gates", "opportunity.judge", "governance", "skills", "builders", "runtime.policy", "runtime.audit"):
                self.assertNotIn(forbidden, imports)
