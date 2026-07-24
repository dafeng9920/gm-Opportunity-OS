# Phase 18.19 Reality Feedback Report

## Experiment Scope

This experiment ran the existing v0.6.18 runtime slice three times against public Roblox page captures and public statistics captures. It did not add a crawler, Fact definition, Gate rule, Judge capability, scoring, ranking, or recommendation engine.

For every candidate, the exact runtime chain was:

```text
Signal -> Evidence -> Candidate -> MeasurementArtifact -> EvaluationFact
-> FactQualityBoundary -> Gate -> GateAssessmentAsset -> Static Judge
-> audited Triad roles -> TriadDecisionArtifact
```

Each run wrote only derived SQLite artifacts under `.opportunity-os/`:

- `phase-18.19-grow-a-garden.db`
- `phase-18.19-99-nights.db`
- `phase-18.19-natural-disaster.db`

## Candidates Tested

| Experimental segment | Candidate | Place ID | Capture | Public sources | Captured observations |
| --- | --- | ---: | --- | --- | --- |
| High-signal reference | `[🏴‍☠️] Grow a Garden 🌶️` | `126884695634066` | `2026-07-24T00:00:00+00:00` | [Roblox page](https://www.roblox.com/games/126884695634066/Grow-a-Garden), [stats page](https://www.robloxgames.org/stats/grow-a-garden) | title, creator, description; public stats capture: 35.0B+ visits, 112,548 active players, 10,744,784 favorites |
| Ambiguous comparator | `[🦖] 99 Nights in the Forest 🔦` | `79546208627805` | `2026-07-24T00:00:00+00:00` | [Roblox page](https://www.roblox.com/games/79546208627805/99-Nights-in-the-Forest), [stats page](https://www.bloxquiz.gg/stats/99-nights-in-the-forest) | title, creator, description; public stats capture: 27.6B visits, 339K concurrent players, 8.8M favorites; source reports a 7-day change of -11% |
| Lower-current-signal / historical-snapshot comparator | `Natural Disaster Survival` | `189707` | `2026-07-24T00:00:00+00:00` | [Roblox page](https://www.roblox.com/games/189707/Natural-Disaster-Survival), [stats page](https://bloxcodes.io/top-games/189707) | title, creator, description; public stats capture: 4.1B+ visits, 4,181 active players, 11,439,357 favorites; source snapshot date 2026-02-26 |

The segments are experimental selection labels only. They are not Opportunity OS conclusions about quality, potential, or recommendation.

## Successful Runtime Paths

All three candidates completed the same verified path:

| Step | Grow a Garden | 99 Nights in the Forest | Natural Disaster Survival |
| --- | --- | --- | --- |
| Signal -> two ledger Evidence records | PASS | PASS | PASS |
| Evidence -> Candidate | PASS | PASS | PASS |
| Evidence -> `MeasurementArtifact` | PASS | PASS | PASS |
| `MeasurementArtifact` -> `available_sources@0.1` EvaluationFact | PASS | PASS | PASS |
| Fact Quality -> AcceptedFact | PASS | PASS | PASS |
| GateAssessmentAsset persisted | PASS | PASS | PASS |
| Static JudgeAssessmentRecord (`STATIC_TEST_ONLY`) | PASS | PASS | PASS |
| Three audited Triad roles; identities released | PASS | PASS | PASS |
| TriadDecisionArtifact | PASS (`READY`) | PASS (`READY`) | PASS (`READY`) |

For every candidate, the runtime persisted two Evidence records, one MeasurementArtifact, one Produced/Evaluation Fact, one AcceptedFact, one Gate Asset, one Static Judge record, three role-audit records, clean identity-release records, and one Triad Decision Artifact.

## Blocked Runtime Paths

All three candidates stopped at the same governance-information boundary:

| Step | Result | Runtime evidence |
| --- | --- | --- |
| `available_sources` -> complete Gate input | BLOCKED | Gate status `UNKNOWN`; reasons: `missing_fact:trend_up`, `missing_fact:keyword_difficulty`, `missing_fact:long_tail_count`, `missing_fact:monetization_path` |
| external visits / active-player observations -> current EvaluationFact | BLOCKED | No existing registered Fact definition or authorized producer maps these observations to any of the four missing Gate facts. |
| `UNKNOWN` Gate Asset -> static Judge / Triad Artifact | PASS by current design | Asset, static Judge record, and Triad Artifact are permitted; this is a governed incomplete-evidence output, not a passed opportunity result. |

## Reality Gap Records

### RG-001

**Location:** `MeasurementArtifact -> EvaluationFact`

**Observed problem:** All three captures contained direct public visits and active-player observations, and one contained an externally reported 7-day change. The only existing authorized transformation applicable to this evidence was `available_sources@0.1`. No registered producer/fact definition can convert those observations into the existing `trend_up`, `keyword_difficulty`, `long_tail_count`, or `monetization_path` inputs.

**Evidence:** runtime outputs in all three experiment databases; every Gate Assessment reported the same four `missing_fact:*` reason codes.

**Classification:** A. Missing capability.

**Suggested future action:** Separately determine whether each missing Gate input has a reproducible measurement definition and permitted public source. Do not treat visits or active-player count as `trend_up` without a defined time-series method and Fact Contract authorization.

### RG-002

**Location:** `Evidence acquisition -> MeasurementArtifact`

**Observed problem:** Third-party public statistics sources expose materially different freshness signals. The 99 Nights page displays a source update age of 652 hours; the Natural Disaster Survival source contains a 2026-02-26 snapshot while the experiment capture occurred on 2026-07-24. The current Evidence record preserves capture/provenance, but the experiment has no common freshness rule that can qualify or reject source-observation age.

**Evidence:** source URLs and captured observation payloads above; `.opportunity-os/phase-18.19-99-nights.db` and `.opportunity-os/phase-18.19-natural-disaster.db`.

**Classification:** C. Data acquisition issue.

**Suggested future action:** Before using time-sensitive external values for a Gate Fact, define source-observation timestamp semantics and an allowed freshness window in the relevant future measurement design.

### RG-003

**Location:** `Gate -> Judge -> Triad`

**Observed problem:** `UNKNOWN` Gate status does not block persistence of the Gate Asset, static Judge execution, or Triad Decision Artifact. It produces a controlled incomplete-evidence artifact rather than a completed Gate result.

**Evidence:** all three Gate Assets contain `UNKNOWN`; all three Judge records are `STATIC_TEST_ONLY`; all three Triad artifacts are `READY` with the same static assessment result.

**Classification:** D. Current design intentionally rejects a Gate pass while still allowing governed review output.

**Suggested future action:** Retain this behavior unless a future governance policy explicitly requires incomplete Gate assessments to stop before Judge. That would be a policy decision, not a candidate-specific patch.

### RG-004

**Location:** `EvaluationFact -> Gate`

**Observed problem:** The three candidates have distinct captured scale and freshness observations, but the current Gate receives the same accepted `available_sources` value (`official`, `community`) for each. Their external differences do not affect current deterministic Gate inputs.

**Evidence:** all three runtime Gate assessments have identical missing-fact reasons and no accepted fact derived from visits, active players, favorites, or update metadata.

**Classification:** A. Missing capability.

**Suggested future action:** Use additional real slices to decide which of those observations, if any, should become explicitly defined, evidence-backed Gate measurements. Do not add an aggregate popularity or opportunity score.

### RG-005

**Location:** `GateAssessmentAsset -> Judge`

**Observed problem:** The existing Gate Asset persistence boundary is enforced, but `JudgeInput` still contains the Candidate’s raw `EvidenceObject` tuple. The static runtime therefore has raw evidence available in addition to the asset-derived Gate results.

**Evidence:** existing `opportunity/judge/gate_assembler.py` constructs `JudgeInput(candidate, evidence_items, asset.gate_results)`; confirmed across all three slice runs.

**Classification:** B. Contract boundary issue.

**Suggested future action:** Keep as recorded until a separately authorized Judge Boundary review decides whether strict asset-only Judge input is required. Do not alter the frozen boundary in this experiment.

## Confirmed Existing Strengths

- Evidence IDs remain the persistent lineage anchor from each real capture through Candidate, MeasurementArtifact, EvaluationFact, AcceptedFact, Gate Asset, Judge record, role audit, and Decision Artifact.
- Producer authorization, Fact definition validation, and Fact Quality prevented direct public-stat observations from being mislabelled as unrelated Gate facts.
- Missing Gate inputs are represented as `UNKNOWN`, not converted into a fabricated failure or pass.
- Gate Asset persistence protects the Judge assembler from arbitrary Gate records.
- Static Judge provenance remains explicitly `STATIC_TEST_ONLY`.
- Triad execution emits three append-only audit records and experiment workers finish cleanly released with no active identity binding.

## Missing Capabilities

- Reproducible, authorized measurement paths for the four missing Gate inputs using real Roblox/public-web evidence.
- A standard source-freshness semantics for time-sensitive public statistics evidence.
- If required by future policy, stricter Judge input isolation from raw Evidence.

## Deferred Ideas

- Do not infer growth from one visits/active-player snapshot.
- Do not convert third-party rank, popularity language, or favorites into an opportunity score.
- Do not add fact classes, new Fact IDs, Gate rules, source adapters, LLMs, automation, ranking, or orchestration based on this experiment.
- Do not alter the intentional `UNKNOWN` path without a separate Gate/Judge policy review.

Evidence level: `RUNTIME_VERIFIED`

Verification: `python -m unittest discover -s tests` — 228 passed. `git status --short` shows only this report; experiment SQLite artifacts are under git-ignored `.opportunity-os/`.

