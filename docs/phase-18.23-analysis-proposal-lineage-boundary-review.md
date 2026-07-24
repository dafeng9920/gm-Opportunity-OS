# Phase 18.23 Analysis Proposal Lineage Boundary Review

## Current Provenance Model

The current runtime has three distinct provenance owners.

| Artifact | Identity / references | Current provenance responsibility |
| --- | --- | --- |
| `AnalysisProposal` | `proposal_id`, Candidate ID, MeasurementArtifact IDs, Evidence IDs, requested registered fact/version | Cognition input: summary, assumptions, uncertainty, missing information, and optional future model/runtime/prompt identity. Its status is permanently `NON_AUTHORITATIVE`. |
| `MeasurementArtifact` | `artifact_id`, request, producer/version, fact/version, Evidence IDs | Reproducible measurement: method, captured time, measurements, output, and source provenance. |
| `EvaluationFact` | registered fact/version, value, Evidence IDs, fact provenance | Normalized, evidence-backed Gate fact. It is constructed by `FactProductionBoundary`. |
| `ProducedGateFact` | `production_id`, request, producer/version, MeasurementArtifact ID, EvaluationFact | A production event which binds the producer and its input measurement to the generated Fact. |
| `AcceptedFact` | accepted ID, produced-fact ID, quality assessment ID | Quality acceptance event; it preserves the EvaluationFact rather than adding cognition information. |

`FactProductionBoundary` is the only current Evidence-to-Fact conversion point. It verifies producer registration, supported fact/version, authorized measurement method, exact request/artifact lineage, and Evidence existence. `FactQualityBoundary` then evaluates the produced Fact against a registered quality policy. Neither boundary reads or persists AnalysisProposal references.

Evidence: `opportunity/analysis/contracts.py`, `opportunity/analysis/store.py`, `opportunity/facts/contracts.py`, `opportunity/facts/boundary.py`, `opportunity/facts/store.py`, and `opportunity/fact_quality/boundary.py`.

## Observed Gap

Phase 18.22 runtime verification showed an in-memory chain from a proposal through an authorized-review simulation to a produced Fact. The stored Fact records its MeasurementArtifact ID, Evidence IDs, producer/version, method, and capture time, but contains no `analysis_proposal_id`.

This is not a failure of Evidence provenance: the factual claim remains traceable to its measured Evidence. It is a missing durable link for cognition provenance: a standalone produced Fact cannot show which non-authoritative interpretation requested or motivated its production.

## Option Analysis

### Option A — EvaluationFact provenance

Store `analysis_proposal_id` in EvaluationFact provenance.

Benefits:

- Direct Fact-to-proposal trace in every Fact consumer and persistence copy.
- Simple queries when exactly one proposal is expected per Fact.

Risks:

- Changes the frozen Fact Contract and its required provenance vocabulary.
- Treats a contingent cognition event as part of the factual observation itself.
- One Fact may be reproduced from the same MeasurementArtifact without any proposal, or may be supported by several proposals; one scalar reference cannot represent either case cleanly.
- Gate and Quality consumers would inherit cognition metadata despite having no authority to evaluate it.

Conclusion: direct traceability is attractive, but the ownership is incorrect. A Fact needs to know what it states, how it was measured, and which Evidence supports it. It does not need to define its identity by how somebody proposed it.

### Option B — ProducedGateFact / production wrapper

Store a proposal reference on the production event wrapper.

Benefits:

- Keeps EvaluationFact and Gate input pure.
- Fits the existing producer authorization and `production_id` lifecycle.
- Expresses that a proposal may have triggered one particular authorized production action.

Risks:

- Still changes a frozen production contract/store schema.
- Couples all cognition history to a single production event, while the same proposal may lead to several measurements, reproductions, or rejected attempts.
- Does not naturally represent multiple competing proposals, review outcomes, or a human choosing one of several proposals before production.

Conclusion: better than Option A for a narrow *triggered this production* audit, but too narrow as the primary cognition-history model.

### Option C — Independent Artifact Link

Create a future append-only relationship artifact, conceptually `AnalysisProposalArtifactLink`, outside the Fact Contract. Its references would associate one proposal with one or more MeasurementArtifacts, optional authorized-review records, and one or more ProducedGateFacts. It would not alter Fact value, quality, or Gate eligibility.

Benefits:

- Preserves Fact identity and Evidence provenance without cognition contamination.
- Represents many-to-many relationships: several proposals may inform one production; one proposal may inform several authorized productions.
- Separates proposal creation, review, production, rejection, and reproduction into independently auditable events.
- Supports human, GPT, Kimi, MiniMax, and future multi-agent proposals with the same proposal identity model.
- Allows future query/index tooling to be introduced only when the relationship artifact is actually needed.

Risks:

- Adds a future artifact relationship contract and query path.
- Trace queries require a join rather than reading one Fact payload.
- Link creation must itself be append-only and authorized, or it could falsely imply causation.

Conclusion: this is the correct future ownership boundary. It is not implemented in this phase.

## Recommended Ownership

**Recommendation: Option C — independent cognition-provenance artifact link, introduced later only when a durable analysis runtime exists.**

AnalysisProposal is a cognition property, not a Fact property. It states why an actor requested an interpretation of particular measurements; it does not establish the truth of the resulting Fact. The authorized producer, registered fact definition, Evidence lineage, and independent quality boundary establish that truth claim.

At a later implementation point, a link should identify the proposal, the reviewed MeasurementArtifact(s), the resulting production event(s), a link/event identity, creator/reviewer identity, relationship type, and timestamp. It should never grant production authority or become a substitute for Fact Quality.

## Future Multi-Agent Compatibility

GPT, Kimi, MiniMax, a deterministic analyser, and a human should all create the same class of non-authoritative cognition artifact: an AnalysisProposal with declared model/runtime identity when applicable. Their identities belong to proposal provenance, not EvaluationFact provenance.

Multiple proposals should be allowed to lead to the same EvaluationFact. They may independently request the same registered fact from the same measurement, disagree about assumptions, or be considered during human review. The eventual Fact remains valid or invalid based on its authorized production and quality checks, not on proposal count or model identity.

One proposal should also be able to lead to multiple candidate Facts only through separate, explicit links and separate registered production requests. This supports a future proposal that identifies several independently measurable interpretations without giving the proposal the ability to mint new Fact IDs or bypass fact-specific authorization.

The appropriate conceptual cardinality is therefore many-to-many:

```text
AnalysisProposal(s) -- cognition link(s) -- MeasurementArtifact(s)
                                      \
                                       -- ProducedGateFact(s)
```

This relationship preserves competing and collaborative agent history while keeping Gate consumption limited to AcceptedFacts.

## Migration Risk

No migration is required now; this is a static review only.

Option A has the highest frozen-contract risk because EvaluationFact is copied through production, quality, Gate, Judge, and stored artifacts. Option B has medium risk because it changes the production wrapper and fact-production store but leaves Gate input unchanged. Option C has the lowest impact on frozen governance contracts because it adds a future outer audit relationship rather than changing existing payloads.

Reconsider implementation only when all of the following are true:

1. A real analysis capability can persist an AnalysisProposal before review.
2. A durable authorized-review decision exists, rather than a test-only simulation.
3. A concrete audit or frontend query requires reconstruction after process memory is gone.
4. The relationship semantics and writer authorization are defined without allowing a link to create, alter, or accept a Fact.

## Evidence Level

STATIC_VERIFIED

