# Opportunity Judge Agent v0.1

```
Candidate + Evidence + Gate Results -> Judge Assessment -> Triad Governance
```

The Judge may explain facts, identify risks, and return one bounded recommendation: `SMALL_SCALE_VALIDATION`, `GATHER_MORE_EVIDENCE`, or `NO_RECOMMENDATION`. It has no field for gate overrides, candidate status changes, builder calls, or governance decisions.

v0.1 includes only a deterministic mock to prove contract position. It does not call a model, Hermes, a Runtime, or an external data source. A future isolated runtime must conform to `OpportunityJudge` and pass `OpportunityJudgeRunner` validation.
