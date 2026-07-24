# Multi-Judge / Triad Evaluation Foundation v0.1

Triad is a task-instantiated governance role mechanism, not three permanent Agents or a voting system. Each role declares its scope and emits an immutable `RoleAssessmentRecord` referencing one asset-bound Judge assessment. `TriadEvaluationContext` aggregates records; it is `UNKNOWN` when any required role is absent and is never a final decision.
