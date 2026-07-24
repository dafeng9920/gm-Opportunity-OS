# Phase 18.22 Analysis Proposal Runtime Simulation

## Phase Result

RUNTIME_VERIFIED for one recorded public Roblox candidate: `[Roblox] Grow a Garden` (place `126884695634066`). A manually authored `AnalysisProposal` requested the existing `available_sources@0.1` fact from one existing `MeasurementArtifact`. A deterministic, test-only review simulation verified source references, the declared measurement method, and registered producer support before the existing Fact production and quality boundaries ran.

No model, analysis executor, scoring, recommendation, Gate change, Judge change, Triad change, or frozen contract change was introduced.

## Simulation Path

```text
Recorded Roblox Evidence
  -> SourceInventory MeasurementArtifact
  -> NON_AUTHORITATIVE AnalysisProposal
  -> deterministic authorized-review simulation
  -> registered source-inventory-producer
  -> FactProductionBoundary
  -> FactQualityBoundary
  -> EvaluationFact / AcceptedFact
```

The proposal is manually authored and is not a Fact producer. The actual EvaluationFact continues to be made only by `FactProductionBoundary` using the registered `source-inventory-producer@0.1`.

## Authorized Review Simulation

`DeterministicProposalReview` lives only in `tests/test_phase_18_22_analysis_proposal_runtime_simulation.py`. It is not a reviewer runtime or a production authority. Before returning its ephemeral review record it validates:

- each MeasurementArtifact and Evidence reference exists;
- proposal Evidence IDs are inside the MeasurementArtifact Evidence scope;
- the requested fact/version is supported by the selected registered producer;
- the declared transformation method equals the artifact method and is authorized for that producer support;
- measurement and proposal Evidence lineage agree.

Only the subsequent existing `FactProductionBoundary.produce()` call creates the EvaluationFact.

## Boundary Checks

The runtime tests reject:

- an unknown producer;
- a registered producer requesting an unsupported existing fact (`trend_up@0.1`);
- an undeclared transformation method;
- fabricated MeasurementArtifact or Evidence references;
- an unknown new fact ID and a changed unavailable version;
- `recommendation` and `hidden_score` schema fields.

An AnalysisProposal has no conversion API to EvaluationFact, AcceptedFact, Gate input, Judge input, or DecisionArtifact, and Gate evaluation rejects it as an AcceptedFact lookup.

## Provenance Verification

Within this simulation, the trace is demonstrable as:

```text
EvaluationFact / ProducedGateFact
  -> MeasurementArtifact ID
  -> AuthorizedReview.proposal_id
  -> persisted AnalysisProposal
  -> MeasurementArtifact evidence_ids
  -> persisted Evidence
```

The existing produced Fact persists its MeasurementArtifact, Evidence, producer, version, method, and captured-time provenance. It does **not** persist `analysis_proposal_id`. Therefore a reviewer can reconstruct the simulated trace using the retained review record and proposal store during this test, but a standalone produced Fact cannot independently prove which AnalysisProposal initiated it.

## Quality Verification

The existing `available-sources-quality@0.1` policy accepts the produced Fact: the artifact has two Evidence records, explicit source classifications, `source_inventory` measurement data, and method/capture provenance. The accepted output is an `AcceptedFact`; it is not a recommendation or opportunity decision.

## Findings

- The intended authority boundary holds: a proposal can request a registered fact but cannot create it.
- The existing production boundary remains the enforcement point for producer registration and supported measurement methods.
- Reality-derived Evidence and a MeasurementArtifact can traverse a non-authoritative proposal step without bypassing Fact Quality.
- Provenance has one recorded limitation: the frozen EvaluationFact/ProducedGateFact path has no durable `analysis_proposal_id` reference. This is a discovered audit-link gap, not a change made in this phase.

## Evidence Level

RUNTIME_VERIFIED

