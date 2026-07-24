# Triad Decision Artifact Foundation v0.1

`RoleAssessmentStore` is the source of truth for role assessments; `TriadEvaluationContext` is only a reference set. The Writer reloads every referenced record and rejects missing, unpersisted, legacy-unbound, Candidate-mismatched, Asset-mismatched, or duplicate role input.

This is an Opportunity Evaluation Triad instance, not a system-level worker pool or three fixed Agents. `TriadDecisionArtifact` is not an OpportunityDecision. Complete compatible roles produce `READY`; missing roles produce `UNKNOWN`; structured conflicts produce `REVIEW_REQUIRED`. Conflict is never resolved by a 2:1 vote.
