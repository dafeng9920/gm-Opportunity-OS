# Opportunity Gate Engine v0.1

The Gate Engine is deterministic admission code, not an opportunity judge. It evaluates supplied facts against versioned generic rules and returns only `PASS`, `FAIL`, `UNKNOWN`, or `BLOCKED`.

```
Candidate Packet -> Gate Engine -> Gate Results -> future Opportunity Judge Agent -> Triad Governance
```

It never changes a Candidate status, writes Evidence, invokes a Runtime/Agent, or issues a governance decision. `GateResultStore` is append-only history of the exact gate and version used, making historical assessments reproducible.

Implemented v0.1 gates: demand (`trend_up`), competition (`keyword_difficulty <= 30`), content expansion (`long_tail_count >= 10`), data availability (both `official` and `community`), and monetization (a non-empty path exists). These are generic field contracts, not Roblox or SEO rules.
