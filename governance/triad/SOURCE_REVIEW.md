# GM-Lite source review and adaptation record

Reviewed before implementation (read-only):

- `D:\gm-lite\.claude\skills\gm-triad-dispatch\SKILL.md`
- `D:\gm-lite\.claude\skills\gm-triad-prompt-checklist\SKILL.md`
- `D:\gm-lite\TRIAD_ROLE_BOUNDARY_PROMPT_TEMPLATE.md`

Preserved as principles: fixed dispatch inputs, pre-dispatch readiness checks, ordered independent review, and refusal to substitute a missing upstream role.

Adapted: the source's prompt-oriented workflow becomes typed `GovernanceTask`, `RoleArtifact`, and `GateDecisionRecord` contracts.

Intentionally not copied: GM-Lite-specific shell text, project-memory/dogfood instructions, rollout language, and all implementation/business execution instructions. No source file from GM-Lite is imported or copied into this repository.
