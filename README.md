# Opportunity OS

An evidence-driven, governed opportunity pipeline: external signals become hashed evidence, evidence becomes versioned facts, facts feed deterministic gates and a judge boundary, and accepted assessments produce governed evaluation artifacts.

The **core is minimal and business-agnostic**; real capabilities 鈥?collectors, domain plugins, evaluation 鈥?enter one explicit, tested boundary at a time. There is **no real LLM/Agent runtime yet** (the judge layer is deterministic/static), no content generation, no revenue analysis, and no Hermes integration.

## Pipeline

```
external signal -> Evidence (SHA-256) -> governed Facts -> Gate Assessment -> Judge boundary -> Triad evaluation -> Governed evaluation artifact
```

Each arrow is an explicit boundary with its own contract doc and tests. Controlled capabilities already in: a narrow **YouTube RSS** real collector ([real-signal-source-layer](docs/real-signal-source-layer.md)) and an assessment-only **roblox** domain plugin ([opportunity/domains/roblox](opportunity/domains/roblox)).

## Run the verified example

```powershell
python -m tests.runtime_flow
python -m unittest discover -s tests -v
```

The runtime flow creates a local SQLite ledger and generated Mermaid diagrams under `.opportunity-os/`. Those files are derived artifacts and are ignored by Git.

## Core contract

`EvidenceObject` retains the original reference and a SHA-256 content hash. `CandidatePacket` only carries evidence IDs, so evidence remains the ledger's source of truth. Candidate status is advanced solely through the deterministic state machine. A `HANDOFF` transition writes a traceable queue item.

See [docs/contracts.md](docs/contracts.md) and [docs/architecture.md](docs/architecture.md).

## Crawler contract verification

```powershell
python -m tests.runtime_crawler_contract
```

This command verifies the acquisition boundary using an in-process mock adapter only. It does not install or contact a real crawler.
