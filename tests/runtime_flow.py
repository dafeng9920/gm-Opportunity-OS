"""Executable proof of the v0.1 flow, using only local SQLite."""
from pathlib import Path

from candidates import CandidateRepository
from core.mermaid import write_diagrams
from core.queue import HandoffQueue
from core.registry import ComponentRegistry
from core.schemas import CandidatePacket, Component, EvidenceObject, HandoffItem
from core.state import CandidateStateMachine
from evidence import EvidenceLedger


def main() -> None:
    artifact_dir = Path(".opportunity-os")
    artifact_dir.mkdir(exist_ok=True)
    database = artifact_dir / "opportunity-os.db"
    if database.exists():
        database.unlink()

    registry = ComponentRegistry(database)
    registry.register(Component("source.manual", "Manual Signal Source", "data_source", "0.1.0", "active", "captures external signals"))
    registry.register(Component("governance.handoff", "Handoff Consumer", "agent", "0.1.0", "active", "receives candidate packets"))

    evidence_ledger = EvidenceLedger(database)
    evidence = EvidenceObject(
        source="manual-sample", source_type="url", raw_reference="https://example.test/external-signal",
        metadata={"captured_by": "runtime_flow"},
    )
    evidence_ledger.append(evidence)

    candidates = CandidateRepository(database)
    packet = CandidatePacket("Example opportunity", "A manually captured external signal", (evidence.id,), "manual-sample", 0.7)
    candidates.create(packet)

    # Prior signal states are deterministic and may be held by a producer before packet creation.
    state = CandidateStateMachine("DISCOVERED")
    for target in ("COLLECTING", "EVIDENCE_READY", "CANDIDATE_CREATED"):
        state = state.transition_to(target)
    assert state.status == packet.status

    packet = candidates.transition(packet.id, "HANDOFF")
    queue = HandoffQueue(database)
    queue.enqueue(HandoffItem(packet.id, producer="source.manual", consumer="governance.handoff"))
    assert len(queue.pending_for("governance.handoff")) == 1

    write_diagrams(registry, artifact_dir / "diagrams")
    print(f"Runtime flow verified: evidence={evidence.id}, candidate={packet.id}, status={packet.status}")
    print(f"Generated diagrams: {(artifact_dir / 'diagrams').resolve()}")


if __name__ == "__main__":
    main()
