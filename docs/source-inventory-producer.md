# Deterministic Source Inventory Producer v0.1

`source-inventory-producer@0.1` is the first deterministic producer approved for a real Gate Fact. It measures only `available_sources@0.1`; it does not fetch pages, infer demand, or make an opportunity decision.

Its input is selected, persisted Evidence IDs. The producer reads each Evidence object's `source`, `source_type`, and original `raw_reference`, then applies an explicit source-type classification table. The v0.1 table classifies `official-game-entity` as `official` and `community-update-log` as `community`. An unknown source type is rejected rather than guessed.

The output is a `MeasurementArtifact` with `source_records`, followed by the existing Fact Production Boundary, Fact Quality Boundary, and Accepted Fact Store. The quality policy requires the multi-evidence provenance defined by `available_sources@0.1`. Only the resulting `AcceptedFact` can be supplied to Evaluation.

This verifies one data-availability fact only. A full Candidate evaluation remains incomplete until the other four required facts have independently been produced and accepted.