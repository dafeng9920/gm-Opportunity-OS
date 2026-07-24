# Fact Production Boundary v0.1

A Collector acquires raw source observations. It cannot produce an Evaluation Fact by placing data in `DiscoveryRecord.metadata`.

```text
Ledger Evidence IDs
¡ú FactProductionRequest
¡ú registered FactProducer
¡ú MeasurementArtifact
¡ú FactProductionBoundary
¡ú ProducedGateFact (append-only store)
¡ú EvaluationContext
```

A producer is independently registered with its version, supported `fact_id@version` values, and permitted measurement methods. The boundary verifies that the request, artifact, producer support, and persisted Evidence IDs match exactly before it constructs an `EVIDENCE_BACKED` `EvaluationFact`.

This foundation does not execute a producer, collect data, install an API client, or change Gate Rules. It only establishes who may interpret existing Evidence and how that interpretation remains traceable.