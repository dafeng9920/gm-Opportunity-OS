# Opportunity OS

The minimal, business-agnostic foundation for turning external signals into evidence-backed candidate packets and handing them to the next responsible component.

This v0.1 intentionally includes no crawler, agent framework, business plugin, content generation, revenue analysis, or Hermes integration.

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
