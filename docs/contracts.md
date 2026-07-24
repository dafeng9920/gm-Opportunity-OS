# v0.1 contracts

## EvidenceObject

Evidence is immutable on write and retains `source`, `source_type`, `captured_time`, and `raw_reference`. `content_hash` is SHA-256 of `raw_reference`; `metadata` is structured supplemental context, never a replacement for the original reference.

## CandidatePacket

Candidate packets reference the ledger through non-empty, unique `evidence_ids`. `confidence` is bounded to 0..1. The packet has no embedded AI summary requirement and no domain-specific fields.

## Handoff

Moving a candidate into `HANDOFF` must be accompanied by a `HandoffItem` written to the local queue. Each item tracks producer, consumer, candidate, time, and queue status.

## Gate Facts v0.1

Gate evaluation inputs are versioned facts, distinct from raw Evidence and Gate decisions. See [docs/gate-fact-contracts.md](gate-fact-contracts.md).

## Fact Production Boundary v0.1

Collectors persist raw Evidence only. Registered Fact Producers create persisted, validated Gate Facts from that Evidence; see [docs/fact-production-boundary.md](fact-production-boundary.md).

## Fact Quality Boundary v0.1

Produced Facts are not Gate inputs until an independent deterministic quality assessment accepts them; see [docs/fact-quality-boundary.md](fact-quality-boundary.md).

## Deterministic Source Inventory Producer v0.1

The first real Fact producer measures `available_sources@0.1` from persisted Evidence only. It emits a Measurement Artifact; it does not bypass Fact Quality or access external systems. See [docs/source-inventory-producer.md](source-inventory-producer.md).
