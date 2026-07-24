# Gate Fact Contracts v0.1

A Gate Fact is a versioned, deterministic evaluation input. It is neither raw Evidence nor a Gate decision.

```text
Evidence references + required provenance
¡ú GateFactValidator
¡ú Evidence-backed EvaluationFact
¡ú EvaluationGateAdapter
¡ú Gate Engine
```

The v0.1 registry defines five facts: `trend_up`, `keyword_difficulty`, `long_tail_count`, `available_sources`, and `monetization_path`.

Every accepted fact has a fact version, category, typed value, non-empty provenance fields, and Evidence references owned by the Candidate. The validator defines each required provenance set and whether a fact is supported by one or multiple Evidence records.

`available_sources` is explicitly multi-evidence: it requires at least two Evidence IDs. Its value remains subject to the unchanged Gate Rule, which requires both `official` and `community`.

This contract does not collect data, interpret raw sources, alter Gate Rules, or determine opportunity value. A Collector can only propose raw Evidence; it cannot make a Gate Fact eligible without satisfying this boundary.