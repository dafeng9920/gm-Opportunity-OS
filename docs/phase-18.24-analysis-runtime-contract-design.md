# Phase 18.24 Analysis Runtime Contract Design

## Current Boundary

The approved future path is:

```text
MeasurementArtifact
  -> Analysis Runtime
  -> NON_AUTHORITATIVE AnalysisProposal
  -> future cognition-provenance link
  -> authorized FactProducer / review
  -> FactProductionBoundary
  -> FactQualityBoundary
  -> EvaluationFact
```

`AnalysisProposal` is an immutable, append-only cognition artifact. It references a Candidate, MeasurementArtifacts, Evidence, and an already registered requested fact/version. It includes assumptions, uncertainty, missing information, optional model/runtime/prompt identity, and a fixed `NON_AUTHORITATIVE` status. `AnalysisProposalReferenceValidator` validates that referenced Measurements and Evidence already exist and that Evidence is within Measurement scope. The proposal store has append and get only.

`MeasurementArtifact` owns measurement method, producer identity/version, Evidence references, captured time, output, and measurement provenance. `EvidenceObject` remains the source of raw observation. The Fact production, quality, Gate, Judge, Triad, and decision paths do not read AnalysisProposal artifacts.

Evidence: `opportunity/analysis/contracts.py`, `opportunity/analysis/reference_validator.py`, `opportunity/analysis/store.py`, `opportunity/facts/contracts.py`, and `core/schemas.py`.

No contradiction requires changing the frozen AnalysisProposal Contract in this phase.

## Runtime Input Contract

A future Analysis Runtime invocation may receive only a constrained request containing:

- non-empty, existing `measurement_artifact_ids`;
- explicitly permitted, existing `evidence_ids`, each within the referenced MeasurementArtifact Evidence scope;
- one existing Candidate reference;
- one existing registered `requested_fact_id@requested_fact_version`;
- bounded context metadata whose fields, size, and purpose are declared by the runtime contract version.

The invocation receives references, not a capability object. Resolution of those references must be read-only and scoped to the declared Candidate and MeasurementArtifacts. Raw Evidence is supplied only where an explicit context policy permits it; it is never copied into the proposal merely for convenience.

The invocation must not receive a Fact writer, Fact registry writer, Gate state, Gate evaluator mutation interface, Judge input writer, Triad writer, DecisionArtifact writer, or a general database handle. Runtime dependency injection must make those capabilities unavailable rather than relying only on runtime policy.

## Runtime Identity Model

Every invocation must declare the following immutable execution identity before it runs:

| Field | Requirement | Purpose |
| --- | --- | --- |
| `runtime_id` | required | Named analysis-runtime implementation. |
| `runtime_version` | required | Versioned runtime behavior and contract compatibility. |
| `executor_type` | required | `model`, `human`, `deterministic`, or declared graph/multi-agent executor type. |
| `executed_at` | required | Timestamp of the invocation event. |
| `configuration_reference` | required | Immutable reference to the allowed configuration snapshot. |
| `model_identity` / `model_version` | optional pair | Provider/model identity, required together when a model is used. |
| `prompt_reference_id` | optional | Immutable prompt, template, or reference-set identity when applicable. |
| `invocation_id` | required | Unique execution/audit event identity. |
| `idempotency_key` | optional | Caller-supplied retry identity; never a Fact identity. |

Runtime identity describes who produced a cognition proposal; it must not become producer authorization for Facts. A model identity is neither a quality score nor a governance role.

## Output Contract

On successful analysis, the only domain output is exactly one persisted `AnalysisProposal` with:

- `NON_AUTHORITATIVE` status;
- the Candidate, MeasurementArtifact, and Evidence references resolved from the invocation;
- the existing requested fact ID and version;
- an analysis summary, assumptions, uncertainty, and missing-information declaration;
- runtime/model/prompt identity copied only as descriptive cognition provenance where applicable.

The proposal must be append-only, auditable, and reference-valid before persistence. It must not contain raw Evidence copies, Fact values, an authority grant, a recommendation, an opportunity score, or an implicit confidence-to-decision conversion.

Producing the proposal ends the runtime's authority. Review, cognition-provenance linking, Fact production, Fact quality, and all governance actions are independently invoked later by their respective boundaries.

## Forbidden Capabilities

An Analysis Runtime is permanently forbidden from:

- creating, mutating, accepting, or deleting an `EvaluationFact` or `AcceptedFact`;
- registering Fact definitions, Fact producers, quality policies, or Gate definitions;
- invoking or modifying Gate assessment state;
- creating or mutating Judge inputs, Judge assessments, Triad artifacts, or DecisionArtifacts;
- assigning an opportunity score, recommendation, ranking, approval, or decision status;
- treating model confidence as a governance score;
- creating a new fact ID/version or modifying a requested fact definition;
- bypassing reference validation, authorized human/producer review, FactProductionBoundary, or FactQualityBoundary.

These are capability boundaries, not merely prohibited text fields: the runtime process should not be given writers or service interfaces that could perform them.

## Failure Semantics

| Condition | Required result |
| --- | --- |
| Invalid, fabricated, or out-of-scope reference | Reject before execution; create no AnalysisProposal. |
| Candidate unavailable or inconsistent with input scope | Reject before execution; create no AnalysisProposal. |
| Requested fact/version is unregistered | Reject before execution; create no AnalysisProposal. |
| Runtime implementation/provider failure | Create no AnalysisProposal; record a failed execution audit event with sanitized error class and input/identity references. |
| Partial, malformed, or reference-invalid proposed output | Reject the whole output; create no partial AnalysisProposal; record a failed execution audit event. |
| Persistence failure | Do not claim success; record or surface a failure outcome only where an audit store can do so atomically/reliably. |

Recommendation: failures are execution audit events, not failed AnalysisProposal artifacts. A proposal is a meaningful, reviewable cognition claim; an incomplete payload or provider error is not one. A future append-only execution-audit artifact may record attempted input references, runtime identity, outcome, sanitized error category, and timestamp without acquiring governance authority.

## Idempotency

The same semantic input should not be assumed to create an identical proposal: models can be nondeterministic, configuration may change, and a human may make a different bounded interpretation. Every intentionally new successful invocation is therefore a new cognition event with a new `proposal_id` and `invocation_id`.

Transport retries are different from new analysis. A supplied `idempotency_key`, bound to a canonical request fingerprint plus runtime/version/configuration reference, should return the already recorded invocation outcome rather than silently running again. This permits at-most-once proposal persistence for a retry without conflating independently requested cognition events.

Deterministic runtimes may additionally publish reproducibility metadata or an output digest, but that metadata must not turn proposal equality into Fact identity or Fact acceptance.

## Audit Requirements

A future append-only runtime execution audit must record:

- invocation and optional idempotency identities;
- input Candidate, MeasurementArtifact, and permitted Evidence references;
- requested registered fact/version;
- runtime identity and configuration/prompt reference identities;
- start and completion/failure timestamps;
- outcome (`SUCCEEDED`, `REJECTED_PRE_EXECUTION`, or `FAILED_EXECUTION` as future contract-defined states);
- successful output `proposal_id`, if any;
- sanitized failure category and retry relationship, if any;
- a future cognition-provenance link reference when one is created.

The audit record is evidence of execution, not evidence that an interpretation is true. It must not be read by Gate or used as an alternative path into a DecisionArtifact.

## Multi-Agent Compatibility

GPT, Kimi, MiniMax, a local deterministic component, a human analyst, and a graph/multi-agent runtime each implement the same outer Analysis Runtime Contract. They differ only in `runtime_id`, `runtime_version`, `executor_type`, configuration identity, and optional model/prompt identities.

A graph or multi-agent runtime may record its graph configuration as the configuration reference and emit one or more independent invocation/proposal events. It must not collapse internal model votes, confidence, or delegation into a hidden Gate signal. Multiple proposals remain competing or complementary cognition artifacts; later authorized review decides whether any requested registered Fact should be reproduced.

## Recommendation

Adopt this design as the minimum future Analysis Runtime boundary, with no implementation in this phase.

Intelligence may read explicitly scoped reality-derived references and speak only by writing a non-authoritative AnalysisProposal. It may not receive governance writers, and its successful output does not cause Fact production. Durable execution audit and cognition-provenance linking should be designed and accepted before the first model provider is integrated.

## Evidence Level

STATIC_VERIFIED

