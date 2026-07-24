# Phase 18.27 External Intelligence Boundary Design

## Current Safe Runtime

The verified Analysis layer has a deliberately narrow, non-intelligent container:

```text
MeasurementArtifact / permitted Evidence / Candidate reference
  -> Analysis Runtime request
  -> NON_AUTHORITATIVE AnalysisProposal
  -> CognitionProvenanceLink
  -> separate authorized Fact production and quality boundaries
```

`DeterministicAnalysisRuntime` only reads scoped references, writes an append-only AnalysisProposal and its execution audit, and has no Fact, Gate, Judge, Triad, or decision writer. `CognitionProvenanceLink` records a Proposal's independent relationship to later real production events without becoming Fact provenance.

The same authority boundary applies to every future external intelligence source. A model may add cognition; it may not convert cognition into governance state.

Evidence: `docs/phase-18.24-analysis-runtime-contract-design.md`, `opportunity/analysis/runtime.py`, `opportunity/analysis/contracts.py`, `opportunity/analysis/cognition.py`, `opportunity/facts/boundary.py`.

## External Entry Point

Three possible placements were reviewed.

| Option | Benefits | Risks |
| --- | --- | --- |
| A. External Model -> Analysis Runtime Adapter -> AnalysisProposal | Smallest path; adapter can validate a structured response. | Loses the original model response unless it is separately retained; later parsing disputes are hard to audit. |
| B. External Model -> Raw Output Artifact -> Analysis Runtime Adapter -> AnalysisProposal | Preserves immutable model output separately from normalized cognition; enables re-parsing, incident review, and model/provider comparison. | Adds one future raw-output artifact and retention/security policy. |
| C. External Model -> Cognition Event -> AnalysisProposal | Concise conceptual event stream. | Conflates provider execution, raw response, normalization, and proposal persistence; weakens failure attribution. |

**Recommendation: Option B.** A future provider adapter invokes the external model through the Analysis Runtime boundary and persists an immutable, access-controlled Raw Output Artifact before normalizing a valid response into AnalysisProposal. The raw artifact is execution provenance, not Evidence, Fact, Gate input, or a decision. The adapter is still prohibited from calling Fact production.

```text
External model
  -> provider adapter inside Analysis Runtime capability boundary
  -> RawOutputArtifact (immutable, restricted)
  -> proposal normalizer / reference validator
  -> NON_AUTHORITATIVE AnalysisProposal
```

## Input Envelope

The minimum external request envelope contains only:

- `invocation_id`, runtime ID/version, and configuration reference;
- Candidate ID;
- non-empty selected MeasurementArtifact IDs;
- explicitly permitted Evidence IDs within the selected Measurement scope;
- one registered requested `fact_id@version`;
- a bounded task instruction and bounded context metadata;
- model/prompt/tool configuration references, not open-ended capability handles.

Reference resolution is read-only. The provider receives only the material selected by a context policy; it does not receive a database connection, a Fact writer, Fact registry writer, Gate state, Judge assessments, Triad state, DecisionArtifacts, or an authenticated internal service token capable of changing governance state.

Raw Evidence should be minimized: provide the MeasurementArtifact first, and include raw Evidence only when the declared task needs it. Inputs must be size-bounded, classified, redacted where required, and recorded by reference and content digest. Prompt instructions must explicitly say that output is a non-authoritative proposal, not an opportunity conclusion.

## Output Envelope

External output has two separate layers.

1. **RawOutputArtifact** — immutable provider response reference/digest, provider request identity, timestamps, transport metadata, and any safe structured-response parse result. Access is restricted because provider output can contain sensitive or untrusted content.
2. **AnalysisProposal** — the only normalized domain output. It remains append-only and `NON_AUTHORITATIVE`, and includes only allowed proposal fields: source references, registered requested fact/version, summary, assumptions, uncertainty, missing information, and descriptive model/runtime/prompt identity.

The future adapter must add an execution-audit record that joins invocation identity, RawOutputArtifact reference, normalized Proposal ID (if successful), and outcome. It must not write EvaluationFact, AcceptedFact, Gate assessment, Judge assessment, Triad artifact, or DecisionArtifact.

Required identity/provenance fields are:

- runtime ID/version and adapter version;
- provider/model identity and exact model version or provider release reference;
- prompt template/reference identity and a digest of rendered permitted inputs;
- configuration reference, declared tools and tool versions, execution environment/version, and policy version;
- invocation/request IDs, start/end timestamps, timeout/retry metadata, and RawOutputArtifact identity/digest;
- normalized AnalysisProposal ID and future CognitionProvenanceLink IDs when created.

## Provenance Requirements

A reviewer must be able to answer, without reading a Fact payload:

```text
Which runtime and provider ran?
With which model/prompt/configuration/tools?
Against which Candidate, Measurements, and permitted Evidence?
What immutable provider output was returned?
How was that output normalized into this Proposal?
What review or authorized production event, if any, followed?
```

The provider's raw response must retain an immutable content digest and reference. Retention, encryption, access control, redaction, and provider data-use settings are required future operational policies; they must be declared rather than assumed. CognitionProvenanceLink remains the relation from normalized proposal to later production event. It should not store raw prompts or responses directly.

## Hallucination Controls

Provider output is untrusted text or untrusted structured data. A claim such as “the game is viral” has no Fact meaning.

Required controls:

- closed output schema: unknown fields such as recommendation, score, ranking, or direct Fact value are rejected or preserved only in restricted raw output, never normalized into Proposal authority;
- request-time validation of Candidate, Measurement, Evidence, and registered fact/version references;
- declared assumptions, uncertainty, and missing information are mandatory normalized fields;
- no model confidence is mapped to Fact confidence, Fact quality, or Gate status;
- no output reaches FactProductionBoundary without a separately authorized producer, declared transformation method, exact input lineage, and independent FactQualityBoundary result;
- provider tool calls, if ever allowed, must be declared read-only and separately audited; no tool may be a hidden Fact or governance writer;
- prompt injection in Evidence or model output is treated as untrusted content, not an instruction to the runtime.

Thus a model may propose `trend_up@0.1` for review, but it can never turn “viral” into `trend_up=True`.

## Multi-Model Compatibility

GPT, Kimi, MiniMax, a human analyst, and a graph/multi-agent runtime are equal only as **non-authoritative cognition sources**. They use the same input/output envelope and differ through recorded runtime/provider/model/prompt/configuration identities.

Multiple proposals must coexist. Agreement does not create a Fact, and disagreement is not an error or a score. It is represented by distinct AnalysisProposals with distinct assumptions, uncertainty, raw output references, and later CognitionProvenanceLinks. A human or registered FactProducer/review boundary may consider them, but proposal count, model brand, or model confidence never alters Gate behavior.

A multi-agent graph is one runtime execution environment or several independently audited runtime invocations. It must record graph version, participating executor identities, delegation/tool policy, and aggregation rule. Its aggregate output is still merely one or more AnalysisProposals.

## Failure Semantics

| Event | Required artifact/outcome |
| --- | --- |
| Provider timeout, transport failure, rate limit, or authentication failure | Execution audit with `FAILED_EXECUTION`; no Proposal; RawOutputArtifact only if a response fragment was actually received and retention policy permits it. |
| Malformed provider output or schema violation | RawOutputArtifact plus failed execution audit; no Proposal. |
| Unsupported claim, unknown fact/version, or invalid source reference | Pre-execution rejection audit when detected before provider invocation; otherwise raw-output/normalization failure audit; no Proposal. |
| Partial response | Retain as restricted raw output only when policy allows; failure audit; no partial Proposal. |
| Valid normalized response | RawOutputArtifact, successful execution audit, and one valid non-authoritative Proposal. |

There is no “failed Fact” created by model failure. A failed provider execution is an audit event, not a cognition claim and not a governance event.

## Recommendation

Adopt Option B when external intelligence implementation is authorized: an external provider adapter may exist only inside the existing Analysis Runtime capability boundary, and its sole normalized domain result is AnalysisProposal. Persist raw output separately, normalize through closed schemas and reference validation, then use CognitionProvenanceLink for later review/production relationships.

Before any provider is connected, define the RawOutputArtifact contract, provider credential/isolation policy, data-retention/redaction policy, structured-response schema, tool policy, and execution-audit extension. Do not modify Fact, Gate, Judge, Triad, or Decision contracts to accommodate a provider.

## Evidence Level

STATIC_VERIFIED

