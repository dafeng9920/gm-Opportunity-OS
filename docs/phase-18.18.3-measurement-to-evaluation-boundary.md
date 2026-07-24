# Phase Result

Phase 18.18.3 proves one existing Gate Fact can be created from real Roblox measurements only through the existing authorized transformation chain:

```text
Roblox Evidence
  -> SourceInventoryProducer MeasurementArtifact
  -> FactProductionBoundary
  -> EvaluationFact: available_sources@0.1
  -> FactQualityBoundary
  -> AcceptedFact
  -> MultiFactGateEvaluator
```

The selected Fact is `available_sources@0.1`. It records only the explicit classifications `official` and `community` for the Phase 18.18.1 official Roblox page and public statistics evidence. It does not infer popularity, quality, success, opportunity, or a recommendation.

## Transformation Path

- `opportunity/facts/source_inventory.py`: `SourceInventoryProducer.measure()` reads only ledger evidence, applies an explicit source-type classification map, and returns a `MeasurementArtifact`.
- `opportunity/facts/boundary.py`: `FactProductionBoundary.produce()` is the only production path to `ProducedGateFact` and its `EVIDENCE_BACKED` `EvaluationFact`.
- `opportunity/fact_quality/boundary.py`: `FactQualityBoundary.assess()` independently accepts or rejects a produced fact.
- `opportunity/gate_evaluation/evaluator.py`: `MultiFactGateEvaluator` consumes only `AcceptedFact` records.

## Authorized Producer

`FactProducerRegistry` in `opportunity/facts/registry.py` registers producer identity/version pairs. `SourceInventoryProducer.registration()` authorizes exactly:

- producer: `source-inventory-producer@0.1`
- fact: `available_sources@0.1`
- method: `evidence-source-type-v1`

`FactProductionBoundary` rejects an unregistered producer, unsupported fact ID/version, unsupported method, artifact/request mismatch, and unresolved evidence references before it constructs an `EvaluationFact`.

## Fact Definition Used

`opportunity/evaluation/fact_contracts.py` registers `available_sources@0.1` as:

- category: `DATA`
- value type: non-empty source set
- evidence semantics: multi-evidence
- required provenance: `source_inventory`, `method`, `captured_at`

The phase quality policy independently requires two evidence records and `source_records` measurement data before accepting the fact.

## Provenance Verification

The runtime test traces the result through all persisted references:

- `ProducedGateFact.measurement_artifact_id` identifies the source `MeasurementArtifact`.
- `ProducedGateFact.producer_id` and `.producer_version` identify the authorized producer.
- `EvaluationFact.evidence_ids` reference both original ledger evidence records.
- `EvaluationFact.provenance` carries source inventory, measurement method, and capture time.
- the stored MeasurementArtifact carries source records that name the underlying evidence IDs.

A reviewer can therefore trace the produced Gate Fact back to both Phase 18.18.1 evidence records. Producer and measurement-artifact identity are held by the persisted `ProducedGateFact` wrapper rather than by fields directly on `EvaluationFact`.

## Quality Verification

- With the two classified Roblox evidence records, quality passes and the resulting `AcceptedFact` appears in `MultiFactGateEvaluator` input.
- With the same two evidence records, a structurally valid `available_sources` EvaluationFact is assessed by a separate quality policy requiring an absent measurement field. Quality fails, no `AcceptedFact` is stored, and Gate reports `missing_fact:available_sources`.

This proves that valid structure alone is insufficient for Gate eligibility.

## Boundary Tests

Runtime tests verify:

- registered producer: allow;
- unregistered producer: deny;
- unsupported Fact ID: deny;
- unsupported Fact version: deny;
- MeasurementArtifact passed as a Gate lookup: deny;
- SourceInventoryProducer has no direct `EvaluationFact` writer; it returns MeasurementArtifact only.

## Findings

The authorized reality-to-governance path exists and needs no new Decision Context:

```text
measurement authorization -> fact definition validation -> quality acceptance -> Gate consumption
```

Two frozen-contract observations were recorded, not changed:

1. `EvaluationFact` alone does not carry producer ID/version or measurement-artifact ID. Those identities are preserved by `ProducedGateFact` and the production store.
2. The immutable `EvaluationFact` contract validates required provenance but does not reject extra provenance keys containing judgement language such as `recommendation` or `opportunity_score`. The governing production path and quality/Gate paths do not add those keys, but direct public dataclass construction is not capability-restricted. This phase does not modify the frozen Fact Contract; a later review may decide whether explicit provenance-key allowlisting is needed.

## Evidence Level

`RUNTIME_VERIFIED`

`python -m unittest tests.test_phase_18_18_3_measurement_to_evaluation_boundary -v` — 7 passed
`python -m unittest discover -s tests` — 221 passed




