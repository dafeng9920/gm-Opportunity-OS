# Evidence-backed Evaluation Context Boundary v0.1

This boundary turns a persisted Candidate and its Ledger-owned Evidence into a traceable `EvaluationContext`, then adapts only verified facts to the unchanged generic Gate Engine.

```text
CandidateRepository
↓
EvidenceResolver
↓
EvaluationContext
↓
EvaluationGateAdapter
↓
OpportunityGateEngine
```

Evidence metadata may declare a fact with this shape:

```json
{
  "evaluation_facts": [{
    "fact_id": "trend_up",
    "category": "DEMAND",
    "value": true,
    "confidence": 0.8
  }]
}
```

Every resolved `EvaluationFact` carries the originating Evidence ID. The current generic Gate adapter accepts exactly five verified fact IDs: `trend_up`, `keyword_difficulty`, `long_tail_count`, `available_sources`, and `monetization_path`. The adapter rejects missing, duplicate, category-mismatched, and `UNVERIFIED_INPUT` facts before the Gate Engine runs; unverified input cannot support a PASS result.

`CandidateEvaluationService` retrieves the persisted Candidate, resolves its complete Evidence set, and returns an immutable context, field-level lineage mapping, and Gate assessment. It does not call Judge, Triad, Packet assembly, Consumer layers, Skills, Builder, or Runtime policy. It does not alter Gate rules.
