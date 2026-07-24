# Phase 18.21 AnalysisProposal Contract Design

## Existing Boundary Review

The review reuses, without modifying, these existing boundaries:

- `core/schemas/models.py`: immutable `EvidenceObject` carries raw-source identity, capture time, hash, and metadata.
- `opportunity/facts/contracts.py`: immutable `MeasurementArtifact` carries producer ID/version, method, Evidence IDs, measurements, output, provenance, artifact ID, and capture time.
- `opportunity/facts/registry.py`: `FactProducerRegistry` defines authorized producer/version pairs.
- `opportunity/facts/boundary.py`: `FactProductionBoundary` is the only current production path to an evidence-backed `EvaluationFact`.
- `opportunity/fact_quality/boundary.py`: independent quality acceptance determines whether a produced fact can enter Gate.
- `opportunity/evaluation/fact_contracts.py`: the closed Gate Fact registry validates the requested `fact_id@version`.
- `opportunity/assessments/store.py` and `opportunity/triad_evaluation/store.py`: existing append-only SQLite artifact patterns informed the proposal store.

Reusable patterns are immutable dataclasses, UUID identity, UTC creation time, tuple-only reference sets, append-only SQLite primary keys, persisted-reference reloading, and read-only validation before a higher-authority boundary accepts an artifact.

## Contract Purpose

`AnalysisProposal` is a future cognition-layer artifact. It records a bounded suggestion about whether named MeasurementArtifacts may support an already-defined Gate Fact.

It is append-only, non-authoritative, evidence-scoped, and reviewable. It is not an observation, MeasurementArtifact, Fact, EvaluationFact, AcceptedFact, Gate input, Judge input, Triad input, or Decision Artifact.

The contract intentionally has no model, agent, executor, producer, Gate, Judge, Triad, or decision dependency.

## Schema Design

Implemented contract: `opportunity/analysis/contracts.py`.

| Group | Fields |
| --- | --- |
| Identity | `proposal_id`, `candidate_id`, `created_at` |
| Input references | `measurement_artifact_ids`, `evidence_ids` — immutable IDs only; no copied raw evidence |
| Requested interpretation | `requested_fact_id`, `requested_fact_version` |
| Analysis metadata | `analysis_summary`, `assumptions`, `uncertainty`, `missing_information` |
| Optional future identity | `model_identity`, `model_version`, `runtime_identity`, `prompt_reference_id` |
| Status | `AnalysisProposalStatus.NON_AUTHORITATIVE` only |

The requested Fact ID/version must resolve in the existing closed Gate Fact registry. A proposal therefore cannot define a new Fact ID or version.

`opportunity/analysis/reference_validator.py` supplies a read-only `AnalysisProposalReferenceValidator`. It requires every referenced MeasurementArtifact and Evidence record to exist, and requires proposal Evidence IDs to be within the referenced measurement artifacts’ Evidence scope.

`opportunity/analysis/store.py` provides append-only `AnalysisProposalStore`. It can append and retrieve proposals only; it exposes no update or delete operation.

## Authority Boundary

The proposal has no conversion method and no authority to create any governance artifact.

```text
MeasurementArtifact
  -> AnalysisProposal (NON_AUTHORITATIVE)
  -> future human or registered FactProducer review/reproduction
  -> FactProductionBoundary
  -> FactQualityBoundary
  -> EvaluationFact / AcceptedFact
```

Only an independently authorized future producer/review step may attempt a transformation. It must still satisfy the existing producer registry, Fact definition, FactProductionBoundary, and FactQualityBoundary. The proposal cannot substitute for any of them.

## Reference Integrity Rules

A valid proposal requires:

- non-empty, unique MeasurementArtifact IDs;
- non-empty, unique Evidence IDs;
- every MeasurementArtifact ID to resolve through the supplied read-only lookup;
- every Evidence ID to resolve through the supplied read-only lookup;
- every proposal Evidence ID to occur in the referenced MeasurementArtifact lineage;
- an existing requested `fact_id@version` in the closed Gate Fact registry.

Unknown measurement IDs, unknown Evidence IDs, and Evidence IDs outside the measurement scope are rejected. The contract stores references only and never copies raw Evidence content.

## Forbidden Paths

The proposal contract has no method or import path that can:

- create `EvaluationFact` or `AcceptedFact`;
- become an `AcceptedFact` lookup or enter `MultiFactGateEvaluator`;
- create Gate input, Judge input, Triad context, or a Decision Artifact;
- modify Fact definitions, producer registration, or Gate definitions;
- define a new Fact ID;
- execute a model, agent, analysis executor, or runtime.

The tests verify that passing a proposal to `MultiFactGateEvaluator` is rejected because it is not an `AcceptedFact` lookup.

## Test Results

Created: `tests/test_analysis_proposal_contract.py`

- valid immutable, append-only non-authoritative proposal creation: passed;
- existing MeasurementArtifact/Evidence reference validation: passed;
- unknown or out-of-scope source references: rejected;
- new Fact ID and authoritative status: rejected;
- direct Fact, AcceptedFact, Gate, Judge, Triad, and Decision conversion paths: absent/rejected;
- static import boundary: verified.

Verification:

- `python -m unittest tests.test_analysis_proposal_contract -v` — 5 passed
- `python -m unittest discover -s tests` — 233 passed

## Future Implementation Notes

A future analysis implementation must be a separate, explicitly authorized reader of this contract. It may create a proposal only after a future request/identity/audit design is approved. It must remain read-only with respect to Evidence, Fact, Quality, Gate, Judge, Triad, and Decision stores.

A future implementation still needs a separately approved handoff contract from proposal to human review or a registered FactProducer. It must never treat analysis text, model confidence, or a proposal ID as proof of a Fact.

Evidence level: `STATIC_VERIFIED`
