# Triad Decision Artifact Boundary v0.1

This phase provides a durable destination for a future Triad Runtime decision without implementing that Runtime:

```text
Validated GovernanceTask
¡ý
TriadDecisionArtifact
¡ý
TriadDecisionWriter
¡ý
append-only TriadDecisionStore
¡ý
GovernanceSnapshotFactory
```

`TriadDecisionWriter` validates task ID, Candidate ID, Assessment ID, explicit task input lineage, Compliance issuance, and the complete formal Execution ¡ú Review ¡ú Compliance chain through the existing boundary validator. `FUTURE_TRIAD_RUNTIME` artifacts require audit references. `STATIC_TEST_ONLY` artifacts and snapshots require explicit `test_mode=True`.

`GovernanceSnapshotFactory` only creates a snapshot from a persisted Decision Artifact and carries its `decision_artifact_id`. It does not change `OpportunityPacketAssembler`; manual Packet test fixtures remain static-only until a later packet-governance binding phase.