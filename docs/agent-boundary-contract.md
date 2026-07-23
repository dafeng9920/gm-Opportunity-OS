# Agent Boundary Contract

An Agent may read only supplied context, produce structured output, and request tools allowed by its registered Skill and Runtime Policy.

An Agent may not modify Evidence or Candidates, bypass Gates, call Triad directly, change Runtime Policy, or create state. The Skill Invocation and Output Validator enforce the integration boundary; an Agent is not a system of record.
