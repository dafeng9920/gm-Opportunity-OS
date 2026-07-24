# Judge Runtime Adapter Foundation v0.1

`JudgeRuntimeAdapter` is the sole controlled path from a persisted `GateAssessmentAsset` to `JudgeAssessmentStore`.

```text
GateAssessmentAsset → JudgeInputAssembler → JudgeRuntimeAdapter → JudgeRuntime → AssessmentRecordWriter → JudgeAssessmentStore
```

A runtime receives immutable scoped input and returns a structured `JudgeRuntimeResult`; it cannot provide Facts, alter Evidence, or change Gate results. The Adapter rejects non-contract output, source/metadata mismatches, missing reasoning references, and candidate mismatch before writing.

`StaticJudgeAssessmentRuntime` is only a deterministic contract fixture. Its persisted record remains `STATIC_TEST_ONLY` with runtime source `STATIC_ONLY`; it is not an LLM, Agent, or real Judge Runtime. Future `LLM_RUNTIME`, `HUMAN_REVIEW`, and `TRIAD_REVIEW` are enum declarations only.
