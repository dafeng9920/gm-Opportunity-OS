# Fact Quality Boundary v0.1

A Producer may report a completed measurement; it may not accept its own Fact. A deterministic quality policy evaluates provenance, measurement completeness, evidence linkage, and minimum evidence count before an Accepted Fact reaches Gate evaluation.

```text
ProducedGateFact ¡ú FactQualityAssessment ¡ú AcceptedFact ¡ú Gate
```

Rejected Facts remain append-only, include a rework reference and recommended action, and never appear in the accepted-fact query path.