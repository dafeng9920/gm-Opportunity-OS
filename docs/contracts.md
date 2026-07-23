# v0.1 contracts

## EvidenceObject

Evidence is immutable on write and retains `source`, `source_type`, `captured_time`, and `raw_reference`. `content_hash` is SHA-256 of `raw_reference`; `metadata` is structured supplemental context, never a replacement for the original reference.

## CandidatePacket

Candidate packets reference the ledger through non-empty, unique `evidence_ids`. `confidence` is bounded to 0..1. The packet has no embedded AI summary requirement and no domain-specific fields.

## Handoff

Moving a candidate into `HANDOFF` must be accompanied by a `HandoffItem` written to the local queue. Each item tracks producer, consumer, candidate, time, and queue status.
