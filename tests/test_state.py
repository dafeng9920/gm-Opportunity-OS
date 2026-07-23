import unittest

from core.state import CandidateStateMachine, InvalidTransition


class StateMachineTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        state = CandidateStateMachine("DISCOVERED")
        for target in ("COLLECTING", "EVIDENCE_READY", "CANDIDATE_CREATED", "HANDOFF", "ACCEPTED"):
            state = state.transition_to(target)
        self.assertEqual(state.status, "ACCEPTED")

    def test_rejects_illegal_transition(self) -> None:
        with self.assertRaises(InvalidTransition):
            CandidateStateMachine("DISCOVERED").transition_to("ACCEPTED")
