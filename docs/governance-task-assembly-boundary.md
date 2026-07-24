# Governance Task Assembly Boundary v0.1

`GovernanceTaskAssembler` is the only boundary in this phase that turns a persisted `JudgeAssessmentRecord` into a Triad `GovernanceTask`. It validates the Assessment Record exists, loads its Candidate, requires exact Candidate/Evidence lineage, validates referenced Evidence remains in the ledger, and preserves the Judge Input hash and asset version as task metadata.

```text
JudgeAssessmentRecord
¡ý
GovernanceTaskAssembler
¡ý
Validated GovernanceTask
```

`STATIC_TEST_ONLY` Assessment Records are rejected by default. Tests must opt in with `test_mode=True`; this is not a production authorization path. The assembler does not dispatch Triad, issue a decision, create a `GovernanceSnapshot`, assemble a Packet, or run a Judge.

## Fake Completion Registry

```text
id: FC-002
claim: Governance Approval implemented
actual: GovernanceSnapshot(ALLOW) is test-constructed; no Triad Runtime or decision-to-snapshot source exists
classification: STATIC_ONLY
```