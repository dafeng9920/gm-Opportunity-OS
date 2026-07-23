# CLAUDE.md — Opportunity OS

> Hard constraints for every AI collaborator. Read `README.md` and `docs/contracts.md` before touching code.
> This is a constitution, not a manual: short, hard, non-negotiable. Before extending it, ask whether the new line is truly non-negotiable.

## 1. What this is

A minimal, business-agnostic Opportunity OS foundation: **external signal → evidence → candidate packet → handoff**.
Evidence carries a SHA-256 hash; candidate packets reference evidence by ID only; status advances through a deterministic state machine; handoff writes a traceable queue item.

## 2. First principle: restraint

v0.1 **intentionally includes** no real crawler, no agent framework, no business plugin, no content generation, no revenue analysis, no Hermes integration (mock adapters only).

**"What we do not build" matters more than what we build.** Any new module / dependency / layer of abstraction must first answer: is it required right now? Anything outside the v0.1 scope is rejected. Leaving a directory empty (e.g. `plugins/`, `skills/`) is preferable to filling it for the look of completeness.

## 3. Non-negotiables

1. **One-way dependencies, no cycles.** Keep this layering intact; no lower layer may import a higher one:

   ```
   core          schemas / state / registry / queue / lifecycle / mermaid / contracts   ← foundation
     ↑
   evidence      ledger → core
     ↑
   crawlers.runner → core + evidence      candidates → core (evidence_ids only)
     ↑
   adapters      implement crawlers.contract; hermes / policy self-contained
     ↑
   runtime       audit (standalone); manager / bridges / policy → adapters + core
     ↑
   architecture  engine → core + runtime                                                  ← top aggregation
   ```

   - `core` never imports a business layer (evidence / crawlers / candidates / adapters / agents / runtime / architecture / evaluations).
   - `evidence` does not import crawlers / candidates / adapters / agents / runtime / architecture.
   - `candidates` references evidence via `evidence_ids` and **does not import the `evidence` implementation** — this decoupling is deliberate; do not "helpfully" bridge it.

2. **Evidence is the single source of truth.** `CandidatePacket` carries evidence IDs only, never inlines evidence content.

3. **The state machine is the only entry point for candidate status.** No direct `packet.status = ...`. Transitions live in `core/state/machine.py`.

4. **The Component Registry (SQLite) is the source of truth for what is registered.**

5. **Mermaid diagrams are generated** by `core.mermaid.write_diagrams`. Never hand-edit generated artifacts.

6. **`evaluations/hermes/source/` is vendored third-party reference code, read-only.**
   - It is **not** part of this project, is excluded from coverage, and is not maintained here.
   - **Never** import it into any project module; **never** modify it. Read to reference; do not touch.

## 4. Rules for changing code

- **Definition of done = tests pass, not "I finished writing".** A change to a public contract must come with a test. Run the commands in §6 before claiming done.
- **Do not be over-helpful.** Do not expand scope beyond what was asked; do not introduce new dependencies / frameworks unprompted; do not "incidentally" refactor working code; do not add "missing" features nobody requested. The single biggest lesson from gm-lite is this one: *model over-helpfulness is a greater risk than laziness*.
- **Changes to public contracts** (`EvidenceObject` / `CandidatePacket` / the state machine / `HandoffItem`) **must update `docs/contracts.md` + tests.**
- **No dead code, no TODO accumulation.** Prove a new abstraction is necessary before adding it. Deleting takes more courage than adding — and matters more.
- **AI does not declare "done".** You may report "tests pass, contract updated"; **final sign-off is a human act.**
- **When tempted to break a rule "just this once", stop and ask — do not decide unilaterally.** Every codebase rot is built from such exceptions.

## 5. Extension-point discipline

- `plugins/` and `skills/` are currently empty. **Before filling them, write their contract here or in `docs/` first, then implement.** Empty is a boundary, not an oversight.
- A new adapter = implement the matching contract (e.g. `crawlers.contract`) and register it in the Component Registry.
- New captured signals **must be persisted through `EvidenceLedger`**; no bypass straight into a candidate.

## 6. Verification commands

```bash
python -m unittest discover -s tests       # full unit tests
python -m tests.runtime_flow                # end-to-end runtime + Mermaid generation
python -m tests.runtime_crawler_contract    # acquisition boundary (mock adapter, no network)
```

Generated artifacts land in `.opportunity-os/` (SQLite ledger, Mermaid diagrams); they are derived and git-ignored.

## 7. Where to look

- `README.md` — project positioning and how to run
- `docs/contracts.md` — evidence / candidate packet / handoff contracts (architectural facts)
- `docs/architecture.md` — architecture source of truth (registry / state machine / Mermaid)
