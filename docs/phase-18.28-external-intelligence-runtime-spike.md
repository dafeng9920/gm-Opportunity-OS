# Phase 18.28 External Intelligence Runtime Spike

## Execution Mode

Fixture-only runtime spike. No network calls, provider SDKs, API keys, external credentials, or real model invocation were added. The fixture is persisted as a captured external response and represents an untrusted cognition source.

## Runtime Chain

```text
Captured external fixture
  -> RawOutputArtifact / RawOutputStore
  -> CapturedExternalIntelligenceAdapter
  -> NON_AUTHORITATIVE AnalysisProposal
  -> existing CognitionProvenanceLink (PROPOSED)
```

The adapter stops at Proposal creation. The test records a separate `PROPOSED` cognition link; no Fact production, quality assessment, Gate, Judge, Triad, or Decision path is invoked.

## Raw Output Artifact

`RawOutputArtifact` is immutable and stores `raw_output_id`, provider, model, runtime, capture time, payload reference, execution configuration reference, optional model version, and optional prompt reference. `RawOutputStore` persists the captured payload beside this metadata, append-only, so the original fixture is available for audit before normalization.

Raw output is neither Evidence, Fact, Proposal, nor DecisionArtifact.

## Adapter Boundary

`CapturedExternalIntelligenceAdapter` accepts only a stored artifact ID and Candidate ID. It reads a captured payload, enforces an exact closed Proposal schema, validates Candidate/Evidence scope and existing Measurement/Evidence references, then appends a Proposal only on success.

It has no network behavior and imports no Fact production, Fact quality, Gate, Judge, or Triad modules. It has no Fact, Gate, Judge, Triad, or Decision write method.

## Proposal Generation

The valid fixture includes an existing `trend_up@0.1` request, a stored MeasurementArtifact ID, source Evidence ID, summary, assumptions, uncertainty, and missing information. It creates an append-only `NON_AUTHORITATIVE` AnalysisProposal.

Provider/model/runtime/prompt identity is recorded as cognition provenance on the Proposal, while provider configuration and raw payload identity remain on RawOutputArtifact and the external execution audit. None of these fields enter Fact provenance.

## Provenance Verification

The successful test traces:

```text
raw_output_id
  -> immutable captured fixture payload
  -> external execution audit (proposal_id)
  -> AnalysisProposal
  -> CognitionProvenanceLink(PROPOSED)
  -> MeasurementArtifact -> Evidence
```

The fixture records provider `fixture-external-provider`, model `fixture-model`, model release, adapter runtime identity, configuration reference, and prompt reference. This validates containment and auditability, not analysis quality.

## Rejection Tests

Both a free-text opportunity conclusion and a fixture containing `opportunity_score: 95` are retained as RawOutputArtifact payloads but rejected by the closed schema. Each creates only an external execution audit with `REJECTED` status; neither creates a Proposal.

An unknown Evidence ID is also rejected with audit only. A Proposal cannot be passed to Gate evaluation because it is not an AcceptedFact lookup.

## Findings

The first external-intelligence-shaped input can be captured, preserved, normalized, rejected, and linked without receiving governance authority. The adapter is intentionally a fixture adapter, not a provider adapter. It does not prove model intelligence or provider integration.

## Future Provider Integration

A real provider remains deferred. Before one is authorized, define provider credential isolation, request/response size limits, encryption and retention policy, redaction, transport failure behavior, model/tool policy, and a provider-specific adapter that implements the same closed output boundary. Any real adapter must continue to produce only RawOutputArtifact, execution audit, and NON_AUTHORITATIVE AnalysisProposal.

## Evidence Level

RUNTIME_VERIFIED
