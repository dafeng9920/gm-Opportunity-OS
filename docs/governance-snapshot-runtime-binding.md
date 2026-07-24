# Governance Snapshot Runtime Binding Boundary v0.1

`GovernanceSnapshot` is a derived packet-facing projection, never a source of governance truth:

```text
persisted TriadDecisionArtifact
¡ý
GovernanceSnapshotRuntime validation
¡ý
GovernanceSnapshotFactory
¡ý
derived GovernanceSnapshot
```

The runtime requires the exact immutable Decision Artifact to be present in `TriadDecisionStore`; validates its task/decision, ordered formal RoleArtifacts, Candidate and Assessment lineage, exact flattened audit references, and each audit reference through the injected validator. The Snapshot carries the originating `decision_artifact_id`, Candidate ID, and Assessment ID.

`OpportunityPacketAssembler` now requires a Decision Artifact reference, Candidate match, and Assessment reference. Packet assembly still does not read governance storage: this preserves the one-way boundary. Production callers must obtain snapshots from `GovernanceSnapshotRuntime`; manually constructed test fixtures are explicitly limited to tests.