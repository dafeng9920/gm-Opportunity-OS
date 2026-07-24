# Phase 18.20 Analysis Layer Boundary Review

## Current Architecture

Opportunity OS currently separates reality capture from governance:

```text
Reality -> EvidenceObject -> MeasurementArtifact -> EvaluationFact
-> AcceptedFact -> GateAssessmentAsset -> JudgeAssessmentRecord
-> TriadDecisionArtifact
```

| Layer | Current responsibility | Classification |
| --- | --- | --- |
| Evidence | Immutable raw external observation, source locator, capture time, hash, and metadata. | Observation |
| MeasurementArtifact | Producer-owned, immutable measurement output with source evidence IDs, method, producer identity/version, output value, provenance, and time. | Measurement |
| EvaluationFact | Closed, typed, versioned Gate-input fact with required provenance and evidence semantics. | Interpretation input / governance input |
| FactQuality / AcceptedFact | Independent validation that a produced EvaluationFact has sufficient lineage and measurement completeness. | Authorization / quality control |
| Gate | Deterministic evaluation of only accepted, definition-validated facts. | Decision preparation |
| Judge | Receives a persisted Gate Asset through the existing boundary; current runtime is static-only. | Bounded interpretation |
| Triad | Re-loads role assessments and produces a governed, append-only decision artifact; it is not an OpportunityDecision. | Governance decision artifact |

Evidence:

- `core/schemas/models.py`: `EvidenceObject` is immutable and hash-backed.
- `opportunity/facts/contracts.py`: `MeasurementArtifact` carries measurement identity, producer identity/version, method, evidence IDs, output, provenance, and capture time.
- `opportunity/evaluation/fact_contracts.py`: `DEFAULT_GATE_FACT_REGISTRY` defines a closed, typed set of five Gate facts.
- `opportunity/facts/boundary.py`: `FactProductionBoundary` is the only path that constructs persisted evidence-backed `EvaluationFact` records.
- `opportunity/fact_quality/boundary.py`: only quality-accepted facts proceed to Gate.
- `opportunity/gate_evaluation/evaluator.py`: Gate consumes only `AcceptedFact` records and returns `UNKNOWN` when required facts are missing.
- `opportunity/judge/gate_assembler.py`: Judge input is assembled only from a persisted Gate Asset and accepted-fact scope.
- `opportunity/triad_evaluation/decision_writer.py`: the decision writer re-loads persisted role records and validates candidate/asset scope.

## Existing Capability

The existing system can safely:

- retain real external observations with evidence lineage;
- deterministically measure authorized evidence through registered producers;
- construct only registered Gate facts through `FactProductionBoundary`;
- withhold quality-failed facts from Gate;
- represent incomplete data as Gate `UNKNOWN` rather than inventing a pass/fail;
- persist a Gate Asset, run the explicitly static Judge, and emit an auditable Triad artifact.

Phase 18.19 showed that three real Roblox candidates could complete this governance chain, while all remained `UNKNOWN` because the real captures did not support the four other required Gate facts. The system currently proves integrity and uncertainty handling, not opportunity-analysis capability.

## Missing Capability

The missing capability is not “an LLM that decides opportunities.” It is a controlled way to turn bounded, real measurements into reviewable hypotheses about an already defined Gate Fact when deterministic producer logic is not yet sufficient.

Examples of potentially useful future analysis outputs are:

- a proposal that a specific existing fact may be measurable from named MeasurementArtifacts;
- an explanation of the source observations and transformation assumptions;
- explicit uncertainty, ambiguity, freshness concerns, and conflicting evidence;
- a request for exact missing evidence or an additional deterministic measurement.

The missing capability must not silently convert public visits, player counts, rank language, or free text into `trend_up`, `monetization_path`, `keyword_difficulty`, or an opportunity conclusion.

## Analysis Entry Point Options

### A. Evidence -> Analysis -> Fact

**Benefits:** Direct access to complete source material; may help identify relevant observations.

**Risks:** Highest hallucination and provenance risk. Raw evidence is heterogeneous, stale, and may contain third-party interpretation. An analysis model could confuse extraction with inference, manufacture a Gate value, or bypass the measurement method that makes transformations reproducible.

**Governance impact:** Would blur the Evidence / Measurement boundary and make the model a de facto unrestricted producer.

**Provenance impact:** Every proposal would need exact evidence spans, capture/freshness context, source trust status, and a distinction between quoted observation and model inference.

**Assessment:** Not recommended as the first authoritative entry point. Raw Evidence may be supplied only as explicitly authorized supporting context to a bounded analysis request, never as direct Fact authority.

### B. MeasurementArtifact -> Analysis -> EvaluationFact

**Benefits:** The model receives structured, immutable, producer-attributed measurements rather than arbitrary web text. It can reason about known output values, methods, provenance, source freshness, and missing inputs. This directly addresses the 18.19 gap without changing Gate semantics.

**Risks:** If the arrow means direct Fact creation, it bypasses FactProducer authorization and lets model confidence become an unreviewed score. Measurement values may still be insufficient to support the requested Gate fact.

**Governance impact:** Safe only if the middle result is a non-authoritative, append-only **analysis proposal**, not an `EvaluationFact`.

**Provenance impact:** The proposal must name every MeasurementArtifact and Evidence ID it used, declare its requested `fact_id@version`, explain transformations/assumptions, identify uncertainty, and record model/prompt/runtime identity in a future implementation.

**Assessment:** Recommended future analysis location, with this revised chain:

```text
MeasurementArtifact(s)
  -> bounded analysis proposal
  -> authorized FactProducer / deterministic or human review
  -> FactProductionBoundary
  -> FactQualityBoundary
  -> EvaluationFact / AcceptedFact
```

The Analysis Layer may propose; it has no authority to assert or accept a Fact.

### C. Gate -> Analysis

**Benefits:** The Gate Asset is already compact, persisted, candidate-scoped, and contains known unknowns. Analysis can explain missing inputs or request more evidence without affecting Gate results.

**Risks:** Too late to solve the 18.19 missing-fact problem. It cannot legitimately create absent Fact inputs after Gate without returning to the authorized producer path.

**Governance impact:** Appropriate for post-Gate explanation and information-request analysis only.

**Provenance impact:** Straightforward: input is the persisted Gate Asset plus its declared fact references; output must not alter Gate status or results.

**Assessment:** Useful secondary entry point for future Judge-adjacent explanation, but not the primary analysis boundary for Fact proposals.

### D. Judge only

**Benefits:** Keeps all reasoning late in the chain and preserves deterministic Gate behavior.

**Risks:** Cannot help produce missing Gate facts; risks turning Judge prose into a hidden recommendation or bypass decision. Current Judge Input also includes Evidence objects, so additional isolation work would be required before any future model runtime.

**Governance impact:** Suitable only for bounded interpretation of a persisted Gate Asset after Gate has already determined its status.

**Provenance impact:** Requires a future runtime audit and strict output contract. It must never create an EvaluationFact, Gate Assessment, or Decision Artifact.

**Assessment:** Not sufficient alone for the observed missing capability.

## LLM Boundary Recommendation

**Recommendation: EXTEND LATER at option B, as a proposal-only Analysis Layer.**

A future analysis model may receive a bounded request containing selected `MeasurementArtifact` references, their explicitly permitted supporting Evidence references, the requested existing `fact_id@version`, and a declared task such as “identify whether the supplied measurements are sufficient to propose a reproducible transformation.”

It may produce only:

- a candidate Fact proposal tied to an existing `fact_id@version`;
- cited measurement/evidence references and the exact values used;
- an explanation of assumptions and transformation logic;
- uncertainty, freshness/conflict flags, and missing-information requests;
- a `cannot_propose` result.

It must not produce:

- a direct `EvaluationFact`, `AcceptedFact`, Gate result, Gate Asset, Judge assessment, Triad role result, or Decision Artifact;
- an opportunity decision, recommendation, rank, score, probability, or hidden confidence score used for admission;
- new Fact IDs, altered Fact definitions, or a claim that raw evidence alone is sufficient;
- unreferenced free-text assertions.

Any model confidence may exist only as visible, non-decisive uncertainty metadata within a proposal. It must never become a Gate input, quality score, ranking signal, or default acceptance threshold.

## Fact Generation Authority

An analysis model has **zero Fact-generation authority**.

If it proposes `trend_up`, `monetization_path`, or `keyword_difficulty`, the authority chain remains:

```text
analysis proposal (non-authoritative)
  -> registered FactProducer with declared fact/version/method support
  -> FactProductionBoundary validates producer, request, artifact, evidence, method, and Fact definition
  -> FactQualityBoundary independently accepts or rejects
  -> Gate consumes AcceptedFact only
```

Authority is distributed deliberately:

| Actor / boundary | Authority |
| --- | --- |
| Analysis model | May propose, explain uncertainty, and request missing information. Cannot assert a Fact. |
| FactProducerRegistry | Declares which producer/version is authorized for which `fact_id@version` and method. |
| FactProductionBoundary | Creates the evidence-backed `EvaluationFact` only after authorization and exact lineage checks. |
| Gate Fact Registry / validator | Defines allowed facts, types, evidence semantics, and required provenance. |
| FactQualityBoundary | Independently decides whether a produced Fact is accepted for Gate. |
| Gate | Deterministically evaluates accepted inputs; no model input. |

A future human review may be one implementation of the authorized producer/review step, but must use the same explicit request, evidence lineage, method, and quality path. It cannot accept an LLM response merely because it is persuasive.

## Governance Risks

1. **Judgement leakage:** “good opportunity,” “copy this,” or similar prose may be emitted where only a narrow fact proposal is allowed.
2. **Hidden-score leakage:** model confidence, token probability, ranking, or sentiment may become an undeclared Gate input.
3. **Evidence laundering:** a model may turn stale third-party text into a factual assertion without preserving source timestamp, source kind, or uncertainty.
4. **Method opacity:** a proposal without an executable/reviewable measurement method cannot be reproduced by an authorized producer.
5. **Scope escalation:** allowing analysis to name a new Fact ID or alter a fact definition breaks the closed Gate contract.
6. **Boundary bypass:** direct construction of EvaluationFact-like output would evade producer and quality controls; future implementation must expose no write path from analysis runtime to Fact, Gate, Judge, or Triad stores.
7. **Judge contamination:** using the Judge as a catch-all reasoning layer could turn post-Gate interpretation into an implicit decision engine.
8. **Frontend concealment:** a polished explanation can make `UNKNOWN`, stale data, or missing facts look like a recommendation.

## Future Implementation Requirements

No implementation is authorized by this review. A future proposal must first define and test:

1. A narrow, immutable analysis-request contract that identifies candidate, requested existing `fact_id@version`, allowed MeasurementArtifact/Evidence references, and purpose.
2. A separate, append-only proposal artifact with model/runtime/prompt identity, inputs, source references, explanation, uncertainty, missing-information requests, and explicit non-authoritative status.
3. Read-only access from analysis runtime to the declared inputs; no direct write capability to Evidence, Fact, Quality, Gate, Judge, Triad, or Decision stores.
4. An explicit handoff from proposal to a registered producer or human review; the receiving authority must independently reproduce or reject the proposed transformation.
5. Required provenance fields for every external time-sensitive input, including source-observation timestamp/freshness semantics highlighted by Phase 18.19.
6. Tests proving that analysis output cannot bypass FactProductionBoundary, cannot create a new Fact ID, cannot influence Gate without AcceptedFact, and cannot create a Decision Artifact.
7. A Judge-input isolation review before any model replaces the static Judge runtime, because current `JudgeInput` contains raw Evidence objects.

### Future frontend implication

A frontend should show, separately and visibly:

- confirmed AcceptedFacts and their exact evidence/measurement chain;
- Gate status, missing facts, quality failures, and `UNKNOWN` reasons;
- analysis requests and non-authoritative proposals, with uncertainty and missing-information requests;
- Evidence freshness/source information and conflicts;
- persisted Gate, Judge, role-audit, lifecycle, and Decision Artifact provenance.

It must not collapse a proposal into a confirmed Fact, hide missing inputs behind a score, or present an `UNKNOWN` Gate/STATIC_TEST_ONLY Judge output as a recommendation.

## Decision

**Decision: EXTEND LATER — proposal-only Analysis Layer after MeasurementArtifact and before the existing authorized Fact transformation path.**

This preserves the validated governance chain while creating a future location for intelligence that is useful but non-authoritative. The Analysis Layer can help formulate a reproducible, evidence-scoped measurement proposal; existing Fact Producer, Fact Production, Fact Quality, Gate, Judge, and Triad boundaries retain all authority.

Evidence level: `STATIC_VERIFIED`

Verification: design review only; no code, contract, runtime, or test changes were made for Phase 18.20. The working tree contains the prior Phase 18.19 report plus this Phase 18.20 review.
