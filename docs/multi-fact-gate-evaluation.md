# Multi-Fact Gate Evaluation v0.1

`MultiFactGateEvaluator` accepts one Candidate and only `AcceptedFact` records returned by an Accepted Fact Lookup. Its versioned default policy requires `available_sources`, `trend_up`, `keyword_difficulty`, `long_tail_count`, and `monetization_path`.

It returns an immutable `GateAssessmentRecord` containing fact references, unchanged deterministic Gate results, an overall `PASS` / `FAIL` / `UNKNOWN` status, and machine-readable reason codes. `PASS` requires every required Fact and every Gate to pass. Missing or duplicate required Facts yield `UNKNOWN`; missing data is never treated as `FAIL`. With all required Facts present, a failing Gate yields `FAIL`.

This layer does not read raw Evidence, Measurement Artifacts, or Produced Facts; it cannot modify Facts, run a Judge, rank opportunities, predict revenue, or issue a build recommendation.