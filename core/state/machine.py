from __future__ import annotations

from dataclasses import dataclass

STATES = (
    "DISCOVERED", "COLLECTING", "EVIDENCE_READY", "CANDIDATE_CREATED",
    "HANDOFF", "ACCEPTED", "REJECTED",
)
TRANSITIONS: dict[str, frozenset[str]] = {
    "DISCOVERED": frozenset({"COLLECTING"}),
    "COLLECTING": frozenset({"EVIDENCE_READY", "REJECTED"}),
    "EVIDENCE_READY": frozenset({"CANDIDATE_CREATED", "REJECTED"}),
    "CANDIDATE_CREATED": frozenset({"HANDOFF", "REJECTED"}),
    "HANDOFF": frozenset({"ACCEPTED", "REJECTED"}),
    "ACCEPTED": frozenset(),
    "REJECTED": frozenset(),
}


class InvalidTransition(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CandidateStateMachine:
    status: str

    def __post_init__(self) -> None:
        if self.status not in STATES:
            raise ValueError(f"unknown candidate state: {self.status}")

    def transition_to(self, next_status: str) -> "CandidateStateMachine":
        if next_status not in TRANSITIONS[self.status]:
            raise InvalidTransition(f"cannot transition {self.status} -> {next_status}")
        return CandidateStateMachine(next_status)
