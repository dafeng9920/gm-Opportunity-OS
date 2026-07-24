# Phase 18.18.4 Result

## Runtime Chain

```text
Real Roblox Evidence
  -> SourceInventoryProducer MeasurementArtifact
  -> FactProductionBoundary EvaluationFact (available_sources@0.1)
  -> FactQualityBoundary AcceptedFact
  -> MultiFactGateEvaluator GateAssessmentRecord
  -> persisted GateAssessmentAsset
  -> GateAssessmentJudgeInputAssembler
  -> StaticJudgeAssessmentRuntime / JudgeAssessmentRecord
  -> audited Execution, Review, Compliance role artifacts
  -> released Triad identities
  -> TriadDecisionArtifact
```

The slice uses no LLM, score, ranking, worker pool, orchestration, or new runtime path.

## Components Used

- `opportunity/facts/source_inventory.py`: `SourceInventoryProducer`
- `opportunity/facts/boundary.py`: `FactProductionBoundary`
- `opportunity/fact_quality/boundary.py`: `FactQualityBoundary`
- `opportunity/gate_evaluation/evaluator.py`: `MultiFactGateEvaluator`
- `opportunity/gate_evaluation/assets.py`: `GateAssessmentAssetWriter` and append-only `GateAssessmentAssetStore`
- `opportunity/judge/gate_assembler.py`: `GateAssessmentJudgeInputAssembler`
- `opportunity/judge/static_runtime.py`: `StaticJudgeAssessmentRuntime`
- `governance/triad/execution/`: deterministic role execution and append-only audit records
- `opportunity/triad_identity/`: `TriadIdentityLifecycle`
- `opportunity/triad_evaluation/`: role assessment persistence and `TriadDecisionArtifactWriter`

## Candidate

The runtime candidate is Phase 18.18.1’s real Roblox entity: `[🏴‍☠️] Grow a Garden 🌶️`, place `126884695634066`. The candidate references only its two ledger evidence IDs.

## Evidence Chain

The official Roblox game-page observation and public statistics observation are classified as `official` and `community`. The registered `SourceInventoryProducer` creates the measurement artifact; `FactProductionBoundary` creates `available_sources@0.1`; Fact Quality accepts it only when provenance, measurement records, and the two-evidence requirement are complete.

The slice deliberately creates no synthetic facts for `trend_up`, `keyword_difficulty`, `long_tail_count`, or `monetization_path`.

## Gate Result

`MultiFactGateEvaluator` consumes the real accepted `available_sources` fact. The Gate Assessment is `UNKNOWN`, not `PASS`, because the four other required facts are absent. This is the defined missing-data behavior and avoids manual Gate-input fabrication. The resulting assessment is persisted as a stable `GateAssessmentAsset` that retains the Candidate ID and accepted-fact reference.

A quality-failed `available_sources` fact is not stored as `AcceptedFact`; Gate then reports `missing_fact:available_sources`.

## Judge Result

`GateAssessmentJudgeInputAssembler` accepts only the persisted Gate Asset and verifies Candidate, accepted-fact, and gate-result scope. `JudgeRuntimeAdapter` invokes `StaticJudgeAssessmentRuntime`, producing a persisted `JudgeAssessmentRecord` with:

- `source = STATIC_TEST_ONLY`
- `runtime_id = STATIC_ONLY`
- `runtime_source = STATIC_ONLY`
- `input_asset_id` equal to the persisted Gate Asset ID

No LLM or probabilistic judgement is used.

## Triad Lifecycle

The existing deterministic Execution → Review → Compliance roles run against the real Candidate and persisted Judge assessment ID. Each role creates an append-only audit record. A corresponding Triad worker is bound, executed, and released; all workers finish in `WHITE_STATE` with no active binding and one clean release record.

The persisted role-assessment records bind the same Candidate, Gate Asset, Judge assessment, audit reference, and release-reference provenance. `TriadDecisionArtifactWriter` then persists the decision artifact from those stored records.

## Decision Artifact

The decision artifact references the same Candidate and Gate Asset through its context and role-assessment references. Each persisted role assessment references the same Judge assessment and carries the audit/release provenance. The runtime test walks these references backward to the MeasurementArtifact and ledger Evidence IDs.

## Boundary Failures Tested

- Gate Asset writer rejects a Gate record claiming an absent AcceptedFact.
- Judge assembler rejects an unpersisted Gate Asset.
- Judge assembler rejects a persisted Gate Asset with an unknown Candidate.
- A Fact Quality failure withholds `AcceptedFact` from Gate input.
- `MeasurementArtifact` cannot be supplied as the `AcceptedFact` lookup required by `MultiFactGateEvaluator` (covered by Phase 18.18.3 and unchanged here).

## Findings

The existing components can produce a real, append-only, auditable static decision artifact without widening the frozen contracts. The evidence lineage is complete through persisted stores.

Two gaps are exposed, not repaired:

1. **Judge isolation does not meet the requested strict form.** `GateAssessmentJudgeInputAssembler` requires a persisted Gate Asset, but its existing `JudgeInput` contract includes the Candidate’s `EvidenceObject` tuple. Thus the static Judge has access to raw evidence even though it is invoked through the Asset boundary. Removing that access would change the frozen Judge Boundary.
2. **Triad lifecycle closure is not enforced by the Decision Artifact writer.** The slice explicitly releases every identity and records release provenance, but `TriadDecisionArtifactWriter` does not receive or validate lifecycle state/release records. An unreleased lifecycle is not rejected by that writer today. Adding such enforcement would extend the frozen Triad Decision Artifact / Identity Lifecycle contracts.

## Evidence Level

`RUNTIME_VERIFIED`

- `python -m unittest tests.test_phase_18_18_4_gate_judge_triad_runtime_slice -v` — 7 passed
- `python -m unittest discover -s tests` — 228 passed
