# Triad governance contract v0.1

Input: a `GovernanceTask` with a clear admission objective, immutable input references, and declared output.

Flow: Execution artifact → independent Review artifact → independent Compliance artifact → `GateDecisionRecord`.

The only gate outputs are `ALLOW`, `BLOCK`, and `REVIEW_REQUIRED`. This layer never produces content, discovers opportunities, crawls, writes code, or builds sites.
