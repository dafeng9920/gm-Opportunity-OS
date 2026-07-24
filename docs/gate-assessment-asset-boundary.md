# Gate Assessment Asset Persistence Foundation v0.1

`GateAssessmentRecord` is a deterministic runtime result. `GateAssessmentAsset` is its immutable, append-only persisted projection between Fact Evaluation and the Judgment layer.

```text
AcceptedFact
↓
MultiFactGateEvaluator
↓
GateAssessmentRecord
↓
GateAssessmentAssetWriter
↓
GateAssessmentAssetStore
↓
GateAssessmentJudgeInputAssembler
↓
JudgeInput
```

The Writer re-loads the Candidate, permits only Accepted Fact references within that Candidate's Evidence scope, and rejects incoherent `PASS`, `FAIL`, or `UNKNOWN` status claims. The Store supports `append`, `get`, and `list` only. A JudgeInput can be formed only from an Asset that is already present in that Store; a runtime-only GateAssessmentRecord is not a valid Judge input.

The Asset is not a Fact, does not enter Fact Quality, and does not execute a Judge.
