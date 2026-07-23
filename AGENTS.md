# AGENTS.md — Opportunity OS

> This project is worked on by **multiple AI collaborators** (Claude, Codex / OpenAI Codex CLI, and others).
> **All of them — including you — are bound by [`CLAUDE.md`](CLAUDE.md). Read it first. It is the constitution.**

This file exists so every agent reads the same rules regardless of which instruction file its tooling loads by default (Claude loads `CLAUDE.md`, Codex loads `AGENTS.md`). The two must never drift — `CLAUDE.md` is the single source; this file only points to it and restates the hardest lines.

## Non-negotiable hard lines (full detail in CLAUDE.md §3)

If you read nothing else, do not break these:

1. **One-way dependencies, no cycles.** `core` never imports a business layer. Layering: `core → evidence → {crawlers, candidates} → adapters → {agents, runtime} → architecture`. See CLAUDE.md §3.1.
2. **Evidence is the single source of truth.** `CandidatePacket` carries evidence IDs only, never inlines evidence content.
3. **The state machine is the only entry point for candidate status.** No direct `packet.status = ...`.
4. **Vendored code (`evaluations/hermes/source/` etc.) is read-only.** Never import, never modify, never commit (git-ignored). See CLAUDE.md §3.6.
5. **Generated artifacts (Mermaid under `docs/generated/` and `.opportunity-os/`) are derived, never a second source of truth.** Never hand-edit, never commit (git-ignored). Regenerate via `python -m tests.runtime_flow` or `python -m tests.architecture_flow`. See CLAUDE.md §3.5.

## How to work here

- **Do not be over-helpful.** Stay in scope; no unrequested refactors, dependencies, or "missing" features. (CLAUDE.md §4)
- **Definition of done = tests pass**, not "I finished writing". Run `python -m unittest discover -s tests`. (CLAUDE.md §6)
- **Before pushing:** coordinate with other agents in this repo — do not push over someone else's in-flight changes.
- **If a file changed and you didn't change it**, assume another agent (likely Codex) is working in parallel — not that the user did it.

## See also

- [`CLAUDE.md`](CLAUDE.md) — full constitution
- [`docs/contracts.md`](docs/contracts.md), [`docs/architecture.md`](docs/architecture.md) — architectural facts
