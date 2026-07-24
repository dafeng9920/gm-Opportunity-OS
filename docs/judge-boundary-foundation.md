# Judge Boundary Foundation v0.1

The existing `JudgeInput`, `JudgeAssessment`, and append-only `JudgeAssessmentRecord` contracts remain the system truth. This phase adds a narrow bridge from a `GateAssessmentRecord` to `JudgeInput`.

`GateAssessmentJudgeInputAssembler` re-loads the persisted Candidate, resolves exactly its Evidence IDs, validates Gate result candidate/evidence scope and overall-status coherence, and proves every referenced Gate Fact is an `AcceptedFact` in that Candidate scope. It cannot attach extra Evidence, Facts, or Gate results.

`StaticJudgeAssessmentRuntime` uses the existing deterministic mock only. It emits an append-only `JudgeAssessmentRecord` marked `STATIC_TEST_ONLY` / `STATIC_ONLY`; it is neither an LLM integration nor a real Agent Runtime. The bridge and static runtime cannot alter Facts, create Evidence, change Gate results, call Triad, or produce a business decision.