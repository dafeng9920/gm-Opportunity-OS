# Minimal Agent Principle

Agent capability comes from provided system context, Skill contracts, structured data, allowed tools, and Runtime permissions—not long prompts. Prompts identify a Skill and its input/output only. They do not replace state, Evidence, Gates, contracts, or permission controls.

Every future Agent invocation must be represented by `SkillInvocation` and its output must pass the registered contract validator before it can become an accepted artifact.
