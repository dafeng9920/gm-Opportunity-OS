# Judge Assessment Asset Boundary Foundation v0.1

`JudgeAssessmentRecord` is an immutable, versioned execution-provenance asset around the existing `JudgeAssessment` payload. It does not redefine assessment semantics or execute a Judge.

```text
Validated JudgeInput
↓
Future Judge Runtime
↓
JudgeAssessment
↓
JudgeAssessmentRecord
```

The record binds a canonical `judge_input_hash`, Candidate ID, complete input Evidence and Gate references, Skill and Runtime metadata, audit references, source classification, and record version. `JudgeAssessmentRecordValidator` verifies this lineage against the supplied `JudgeInput`.

`JudgeAssessmentStore` is append-only: it supports `append`, `get`, and `list`; there is no update, overwrite, or delete method. `AssessmentRecordWriter` is the controlled write boundary. It rejects unknown provenance. `STATIC_TEST_ONLY` records must explicitly declare `STATIC_ONLY` runtime metadata. `FUTURE_JUDGE_RUNTIME` records require concrete runtime metadata and audit references, but no such runtime is implemented in this phase.

FC-001 remains in [Judge Input Assembly Boundary](judge-input-assembly-boundary.md): `DeterministicJudgeAgent` is a static contract-verification mock, never a Runtime fact.
