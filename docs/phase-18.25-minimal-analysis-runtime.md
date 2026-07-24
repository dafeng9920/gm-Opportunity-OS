# Phase 18.25 Minimal Analysis Runtime

## Runtime Implementation

Implemented `DeterministicAnalysisRuntime` in `opportunity/analysis/runtime.py`. It is a non-LLM, non-inferential container that accepts a scoped `AnalysisRuntimeRequest`, validates it through existing read-only repositories and `AnalysisProposalReferenceValidator`, writes one `NON_AUTHORITATIVE` AnalysisProposal on success, and writes an append-only `AnalysisExecutionAudit` for every outcome.

The runtime's deterministic output for `trend_up@0.1` is deliberately non-judgmental:

```text
analysis_summary: insufficient deterministic measurements for transformation
missing_information: authorized review and a fact-specific producer are required
```

It does not calculate a fact value, score, ranking, recommendation, or decision.

## Input Boundary

The request contains only Candidate, MeasurementArtifact, and explicitly permitted Evidence IDs; an existing requested fact/version; bounded string context; and an optional idempotency key. Candidate scope, existing Evidence/Measurement references, Measurement-to-Evidence scope, and registered fact/version are validated before a proposal is written.

The runtime receives no FactProductionBoundary, FactQualityBoundary, Gate, Judge, Triad, or decision writer.

## Output Boundary

Success creates only an append-only `AnalysisProposal` with `NON_AUTHORITATIVE` status. Failure creates no proposal; it creates an execution audit with a rejected status and sanitized error category.

The runtime has no Fact, AcceptedFact, Gate, Judge, Triad, or DecisionArtifact write method, and its module imports none of the corresponding production/governance modules.

## Runtime Identity

Every audit records:

- `runtime_id`: `deterministic-analysis-runtime`
- `runtime_version`: `0.1`
- `executor_type`: `deterministic`
- execution timestamp and unique invocation ID
- immutable configuration reference
- request fingerprint, input references, requested fact/version, outcome, and optional proposal ID

The proposal records the runtime identity as descriptive cognition provenance. This deterministic runtime rejects model identity/version, preserving Phase 18.25's non-LLM boundary.

## Proposal Examples

For the recorded Roblox Candidate / MeasurementArtifact test fixture, a valid `trend_up@0.1` request produces a proposal saying that deterministic measurements are insufficient for transformation and that authorized review plus a fact-specific producer are required. The proposal references its Candidate, MeasurementArtifact, and source Evidence; it has no direct Fact value.

## Security / Governance Tests

`tests/test_phase_18_25_minimal_analysis_runtime.py` verifies:

- valid execution produces a non-authoritative Proposal and execution identity;
- runtime → Proposal → MeasurementArtifact → Evidence provenance is traceable;
- no Fact/Gate/Judge/Triad write path or imports exist;
- unknown MeasurementArtifact, unknown Evidence, and unsupported Fact requests are rejected with audit only;
- direct AcceptedFact/Gate request fields are rejected by the closed request schema;
- intentional repeated analysis creates distinct cognition events;
- same idempotency key replays the recorded outcome without a duplicate Proposal;
- the output contains no recommendation or opportunity-score fields.

## Findings

The minimum runtime container works without any intelligent inference. Its meaningful output is an auditable request for later authorized review, not a governance conclusion. This proves that future analysis executors can be constrained by available capabilities rather than being trusted by convention.

A future durable cognition-provenance link remains separate work: the runtime audit records the Proposal identity, while a Fact still has no durable AnalysisProposal link, per the Phase 18.23 decision.

## Future Model Compatibility

A future GPT, Kimi, MiniMax, human, or multi-agent executor must implement this same request/result boundary. It may differ in runtime/model/prompt identity and proposal contents, but it can only append a non-authoritative AnalysisProposal. It must not obtain a Fact writer or governance writer.

## Evidence Level

RUNTIME_VERIFIED
