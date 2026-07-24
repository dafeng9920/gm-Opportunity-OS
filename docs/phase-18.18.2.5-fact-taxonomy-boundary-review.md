# Phase 18.18.2.5 Review

## Current Architecture

The current pipeline deliberately narrows the representation at each boundary:

```text
EvidenceObject
  -> FactProductionRequest
  -> MeasurementArtifact
  -> ProducedGateFact / EvaluationFact
  -> AcceptedFact
  -> GateAssessmentRecord
  -> JudgeInput / JudgeAssessment
```

`EvidenceObject` is the immutable source record. A registered producer turns selected evidence into a `MeasurementArtifact`. `FactProductionBoundary` can then create an `EvaluationFact` only when its identifier and version are registered as gate facts. A separate Fact Quality boundary must accept that fact before the Gate can consume it. Judge input is assembled only from the persisted Gate Assessment and its accepted facts.

This is therefore not one undifferentiated Fact layer. `MeasurementArtifact` already separates producer observation/measurement work from gate-eligible evaluation inputs.

## Evidence

### Gate consumption

Gate consumes only these definition-validated, quality-accepted `EvaluationFact` identifiers:

- `trend_up`
- `keyword_difficulty`
- `long_tail_count`
- `available_sources`
- `monetization_path`

Evidence:

- `opportunity/evaluation/fact_contracts.py`: `DEFAULT_GATE_FACT_REGISTRY` defines exactly those five IDs, with category, typed value, evidence cardinality, and required provenance.
- `opportunity/evaluation/gate_adapter.py`: `EvaluationGateAdapter.REQUIRED_FIELDS` maps exactly the same five IDs to Gate input fields and rejects a context with any required field missing.
- `opportunity/gate_evaluation/contracts.py`: `DEFAULT_GATE_POLICY.required_facts` lists the same five requirements.
- `opportunity/gate_evaluation/evaluator.py`: `MultiFactGateEvaluator` reads only `AcceptedFact` records, ignores facts outside its policy, and passes only required fact values to `OpportunityGateEngine`.
- `docs/multi-fact-gate-evaluation.md`: explicitly states that this layer does not read raw Evidence, Measurement Artifacts, or Produced Facts.

All current `EvaluationFact` records are decision-relevant Gate inputs. They are not a general-purpose catalogue of observed reality. Gate does not require raw Roblox page observations, raw measurement artifacts, unaccepted produced facts, source payloads, or additional facts such as title, creator, place ID, description, visits, or player count.

### MeasurementArtifact boundary

`MeasurementArtifact` can already represent the requested pre-Gate layer:

| Capability | Answer | Evidence |
| --- | --- | --- |
| Raw/selected observation | YES | `measurements` is immutable structured producer output, while `evidence_ids` retain the authoritative raw Evidence references. |
| Measured value | YES | `output_value` is immutable and distinct from the underlying `measurements`. |
| Source provenance | YES | `provenance` is required and immutable; `evidence_ids` are non-empty and unique. |
| Timestamp | YES | `captured_at` is required. Producer-specific source-capture time may also be carried in provenance. |
| Producer identity | YES | `producer_id`, `producer_version`, `request_id`, `fact_id`, `fact_version`, and `measurement_method` are all required. |

Evidence:

- `opportunity/facts/contracts.py`: `MeasurementArtifact` defines the above identity, lineage, method, measurements, output, provenance, and capture-time fields; its post-init freezes all mutable values.
- `opportunity/facts/store.py`: `FactProductionStore.append_measurement()` persists each artifact before any produced gate fact is appended.
- `opportunity/facts/source_inventory.py`: the existing producer emits source records and a measured output without directly accepting a Fact.
- `opportunity/facts/roblox_observations.py`: Phase 18.18.2’s producer proved the same shape against recorded Roblox evidence, including evidence ID, locator, producer identity/version, and capture time.

## Boundary Findings

### Fact Contract purpose

**Finding: B — the current Fact Contract is a specialized Gate-input evaluation-fact model, not a universal reality-fact model.**

Evidence:

- `opportunity/evaluation/contracts.py`: an evidence-backed `EvaluationFact` immediately invokes `GateFactValidator`.
- `opportunity/evaluation/fact_contracts.py`: its registry is closed to five Gate facts and uses Gate-oriented categories (`DEMAND`, `COMPETITION`, `CONTENT`, `DATA`, `MONETIZATION`).
- `opportunity/facts/boundary.py`: the only conversion from `MeasurementArtifact` constructs `EvaluationFact` using `_category_for()`, which looks up the frozen Gate registry.
- `opportunity/fact_quality/contracts.py`: `AcceptedFact` wraps `EvaluationFact`, and `FactLifecycleStatus` ends in `CONSUMED_BY_GATE`.
- `docs/gate-fact-contracts.md`: calls a Gate Fact a “versioned, deterministic evaluation input,” explicitly distinct from raw Evidence and a Gate decision.

The Phase 18.18.2 rejection of `game_title_observed@0.1` is therefore expected enforcement of this specialization, rather than evidence that a generic Fact layer is malfunctioning.

## Options Analysis

### Option C — Keep current architecture

```text
Evidence -> MeasurementArtifact -> (optional future transformation) -> EvaluationFact -> Gate
```

Benefits:

- Matches the existing explicit separation and preserves all frozen contracts.
- Keeps Gate input small, typed, deterministic, and decision-relevant.
- `MeasurementArtifact` already provides the required neutral observation/measurement provenance.
- Avoids promoting every captured source field into a governed Gate fact or allowing raw data to influence Gate/Judge paths.

Risks:

- Neutral measurements are persisted by the production store but have no dedicated first-class cross-producer query/consumption contract outside the production artifact store.
- The word `fact_id` on `MeasurementArtifact` can invite semantic confusion: it identifies the requested measurement, not necessarily a Gate-eligible fact.

Migration cost: none.

Frozen-contract impact: none.

Future extensibility: adequate until a consumer needs stable, cross-producer, non-Gate observation records with explicit lifecycle and query semantics.

### Option A — Extend the Fact Contract with classes

Example: `OBSERVATION`, `MEASUREMENT`, and `EVALUATION` classes under a shared Fact model.

Benefits:

- Gives non-Gate facts a named, first-class taxonomy.
- Could support uniform search, retention, and policy across observation and measurement outputs.
- Makes the semantic distinction visible in one shared contract.

Risks:

- Broadens a currently narrow `EvaluationFact` contract and risks accidentally admitting non-decision data into Gate/quality/Judge paths.
- Requires clear validation, lifecycle, storage, acceptance, and consumer rules for every class; a class field alone does not establish a safe boundary.
- May duplicate `MeasurementArtifact` fields and responsibilities before any consumer demonstrates the need.

Migration cost: medium to high. The existing producer, production store, quality boundary, gate adapter/evaluator, and downstream tests would need compatibility decisions and regression coverage.

Frozen-contract impact: high. It directly changes the Fact Contract and may affect Gate validation and AcceptedFact semantics.

Future extensibility: high, but speculative at the current stage.

### Option B — Split multiple Fact Contracts

Example: separate `ObservationFactContract`, `MeasurementFactContract`, and `EvaluationFactContract`.

Benefits:

- Strongest type-level separation and least ambiguity between observed reality and decision inputs.
- Allows each layer to have its own storage, validators, and lifecycle without making Gate contracts permissive.

Risks:

- Creates multiple new contract boundaries, mappings, stores, and consumers before a second use case establishes their stable shape.
- Produces the largest ownership, versioning, lineage, and migration surface.
- Risks parallel abstractions with responsibilities already covered by Evidence and `MeasurementArtifact`.

Migration cost: high.

Frozen-contract impact: high. It either replaces or surrounds the existing Fact Contract, then requires explicit bridges into the frozen Gate/quality/Judge paths.

Future extensibility: high, but premature without demonstrated consumers that cannot operate on measurement artifacts.

## Recommendation

**KEEP** the current separation.

This is a correct separation boundary, not presently an architectural gap. The existing system already permits real evidence to become immutable, persisted, provenance-complete measurement output. Gate is intentionally restricted to a small, typed, quality-accepted set of decision-relevant `EvaluationFact`s and explicitly does not need raw observations.

Phase 18.18.2 demonstrated that a Roblox observation cannot enter Gate as `game_title_observed`; that is desirable under the current contract because title and creator do not serve one of the existing Gate input fields. Adding a taxonomy now would create a broader model without a demonstrated Gate or non-Gate consumer that needs it.

## Future Trigger Conditions

Reconsider with **EXTEND LATER** only if one or more of the following is demonstrated by a separately scoped real-world slice:

1. Two or more independent producers need to publish the same non-Gate observation with a stable identity and shared query semantics.
2. A governed consumer outside Gate needs to retrieve neutral observations directly, rather than reading a producer-specific `MeasurementArtifact`.
3. Retention, correction, supersession, or quality policy for observations differs materially from both Evidence and the current measurement store.
4. A future Gate requires a new decision-relevant value, and the value has a stable definition, typed semantics, provenance requirements, and a deterministic validation rule. In that case, add a narrowly scoped Gate Fact definition rather than a universal taxonomy by default.
5. The same observation must be safely reused across multiple candidates or domains and current evidence/measurement lineage cannot express the required scope.

Until a trigger occurs, retain the existing chain and treat `MeasurementArtifact` as the controlled observation/measurement boundary outside Gate.
