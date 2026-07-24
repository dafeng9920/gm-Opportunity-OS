# Phase 18.26 Cognition Provenance Runtime

## Runtime Path

The verified runtime path is now:

```text
MeasurementArtifact / Evidence
  -> DeterministicAnalysisRuntime
  -> NON_AUTHORITATIVE AnalysisProposal
  -> append-only CognitionProvenanceLink
  -> existing ProducedGateFact event (optional)
```

`CognitionProvenanceLinkService` records only a validated relationship. It does not invoke `FactProductionBoundary`, Fact Quality, Gate, Judge, Triad, or DecisionArtifact code. Existing authorized Fact production remains a separate action.

## Artifact Design

`CognitionProvenanceLink` is an immutable, independent Analysis-layer artifact with:

- `cognition_link_id` and `created_at`;
- `analysis_proposal_id`;
- scoped `measurement_artifact_ids` and `evidence_ids`;
- `runtime_id` and `runtime_version`;
- status: `PROPOSED`, `REVIEWED`, `PRODUCED`, or `REJECTED`;
- optional review, production-output, and producer-event references.

In this repository, `produced_fact_id` is deliberately the existing persisted `ProducedGateFact.production_id`: EvaluationFact has no standalone persisted identity, while `production_id` is the existing production-output identity. `producer_event_id` optionally records the matching existing FactProductionRequest `request_id`.

Links are persisted in a new append-only `cognition_provenance_links` table. A read-only `FactProductionStore.get_produced()` lookup was added so a link can verify an existing production event rather than claiming production from caller input.

## Relationship Tests

Runtime tests verify all required relationship patterns:

- **Multiple proposals -> one production:** two independently created AnalysisProposals each retain their own link to the same persisted `available_sources@0.1` production event.
- **One proposal -> multiple productions:** one proposal retains distinct links to real `available_sources@0.1` and `trend_up@0.1` production events. The link does not authorize either production; it records their audited relationship after separate registered production calls.
- **Rejected proposal:** a `REJECTED` link remains stored with source lineage and review-event identity but no production reference.

This is a many-to-many cognition history, not Fact identity.

## Provenance Verification

Before recording a link, the service verifies:

- the referenced AnalysisProposal exists;
- its MeasurementArtifact and Evidence references still resolve through the existing validator;
- link Measurement/Evidence IDs are within Proposal scope;
- runtime identity agrees with the Proposal's runtime identity where present;
- a `PRODUCED` link references an existing persisted production output;
- that output's MeasurementArtifact and Evidence are within link lineage;
- an optional producer event ID matches the actual production request.

Unknown Proposal, MeasurementArtifact, Evidence, or production IDs are rejected. A fabricated or mismatched producer-event assertion is rejected.

## Authority Boundary Tests

The link is frozen and append-only: duplicate persistence fails, and neither update nor delete APIs exist. It has no conversion to EvaluationFact, AcceptedFact, Gate input, Judge input, Triad context, or DecisionArtifact. The link service imports none of the Fact production, Fact quality, Gate, Judge, Triad, or assessment modules and has no production or assessment method.

## Findings

The missing cognition-provenance link identified in Phase 18.22 is now independently auditable without adding `analysis_proposal_id` to EvaluationFact provenance or changing Gate input. Evidence provenance and cognition provenance remain separate:

- Fact lineage answers what was measured and produced from which Evidence.
- Cognition lineage answers which proposal, runtime, source Measurements, and subsequent production event were related.

A link records a relationship; it never establishes Fact truth or grants authority. Review-event semantics are intentionally only referenced in this phase because no durable review-event contract exists yet.

## Future Multi-Agent Compatibility

GPT, Kimi, MiniMax, human, deterministic, and graph/multi-agent runtimes can each create independent AnalysisProposals with their own runtime identity. Their proposals may converge on one production event, or one proposal may be related to multiple separately authorized productions. Every relationship remains an append-only link, preserving dissent, collaboration, retries, and rejected interpretations without injecting model identity into Fact or governance contracts.

## Evidence Level

RUNTIME_VERIFIED
