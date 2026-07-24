# Triad Identity Lifecycle v0.1

Triad Workers are white-state execution units. Role, Skill, Permission, and Context are Invocation bindings, never Worker attributes. Release is mandatory; successful cleanup removes the binding and returns the Worker to `WHITE_STATE`. A cleanup failure remains `RELEASE_FAILED`, never falsely white.

Opportunity and Governance Triads are role profiles, not permanent Worker identities. This module is a lifecycle contract, not an orchestrator, worker pool, scheduler, or runtime router.
