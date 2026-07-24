# Phase 18.18.2 — Evidence → Fact Producer Runtime Test

## DONE

The existing Fact Producer runtime was exercised with the Phase 18.18.1 Roblox Evidence. `RobloxObservationFactProducer` extracts direct, source-traceable observations into immutable `MeasurementArtifact` records only:

```text
Ledger Evidence -> RobloxObservationFactProducer -> MeasurementArtifact
```

The runtime test verifies title and creator observations, the originating evidence ID, producer identity/version, source capture time, source locator, and measurement method. It also proves that the frozen Fact Contract rejects conversion of `game_title_observed` into an `EvaluationFact`.

## Existing Fact architecture inspected

- `opportunity/facts/contracts.py`: `FactProducer`, `FactProductionRequest`, `MeasurementArtifact`, and `ProducedGateFact` are immutable production contracts.
- `opportunity/facts/boundary.py`: `FactProductionBoundary.produce()` validates producer registration, method, artifact/request identity, and evidence references before constructing an `EvaluationFact`.
- `opportunity/facts/registry.py`: `FactProducerRegistry` stores authorized producer/version pairs.
- `opportunity/facts/store.py`: `FactProductionStore` persists measurement artifacts and produced gate facts in SQLite.
- `opportunity/evaluation/contracts.py`: `EvaluationFact` is validated by the frozen gate-fact registry when evidence-backed.
- `opportunity/evaluation/fact_contracts.py`: the registry accepts exactly `trend_up`, `keyword_difficulty`, `long_tail_count`, `available_sources`, and `monetization_path`.
- `tests/test_fact_production_boundary.py` and the existing producer tests establish the isolated SQLite and `unittest` conventions.

## Files created

- `opportunity/facts/roblox_observations.py`
- `tests/test_phase_18_18_2_evidence_fact_runtime.py`
- `docs/phase-18.18.2-evidence-fact-runtime.md`

## Files modified

- `opportunity/facts/__init__.py`

## Verification

- `python -m unittest tests.test_phase_18_18_2_evidence_fact_runtime -v` — 4 passed
- `python -m unittest discover -s tests` — 214 passed

Evidence level: `RUNTIME_VERIFIED`

## Discovered friction

The frozen Fact Contract defines only gate-input `EvaluationFact` identifiers. Neutral real-world observations such as `game_title_observed` cannot become a persisted `ProducedGateFact` without adding new fact definitions and categories, which this phase is explicitly forbidden to do. The producer therefore reaches a provenance-complete `MeasurementArtifact`, while the production boundary correctly rejects the conversion. This is a runtime-verified contract gap, not a defect repaired in this phase.


