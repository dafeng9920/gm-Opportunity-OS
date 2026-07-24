# Judge Input Assembly Boundary v0.1

`JudgeInputAssembler` is the only production boundary for constructing a `JudgeInput` from an Evidence-backed evaluation.

```text
CandidateEvaluationResult
↓
CandidateRepository + Evidence Ledger validation
↓
JudgeInput
```

The assembler accepts only `CandidateEvaluationResult`. It re-reads the persisted Candidate, resolves the complete Candidate-owned Evidence set, verifies Context and Gate field lineage, and then constructs the existing `JudgeInput`. A caller cannot attach Candidate, Evidence, or Gate Results separately.

The assembler does not run a Judge, import `OpportunityJudgeRunner`, call an LLM, invoke a Skill Runtime, call Triad, or assemble an Opportunity Packet.

## Fake Completion Registry

```yaml
id: FC-001
claim: Judge Runtime implemented
actual: DeterministicJudgeAgent is a contract-verification mock only
evidence: opportunity/judge/mock_agent.py
classification: STATIC_ONLY
```

`DeterministicJudgeAgent` remains intentional test infrastructure and is not a production Judge Runtime.
