# Phase 18.18.1 — Roblox Candidate Selection & Evidence Acquisition Contract

## DONE

A recorded-public-observation adapter now enters one real Roblox test entity through the existing acquisition boundary:

```text
Recorded public observation -> DiscoveryRecord -> EvidenceLedger -> CandidateFormationService -> CandidatePacket
```

The selected test entity is `[🏴‍☠️] Grow a Garden 🌶️`, Roblox place `126884695634066`. The official page observation records its title, creator (`The Garden Game`), and public description. A separate public statistics observation records visits, active players, and favorites. Neither observation is a fact, score, recommendation, or opportunity conclusion.

## Existing boundaries inspected

- `crawlers/contract.py`: `CrawlRequest`, `DiscoveryRecord`, and `CrawlerPort` define acquisition before Core evidence.
- `crawlers/runner.py`: `CrawlerContractRunner.collect()` validates a registered crawler/adapter and appends `EvidenceObject` records to the ledger.
- `core/schemas/models.py`: immutable `EvidenceObject` stores source, timestamp, raw reference, SHA-256 hash, and metadata; immutable `CandidatePacket` stores only `evidence_ids` for evidence lineage.
- `evidence/ledger.py`: `EvidenceLedger` is append-only SQLite storage for evidence. `.opportunity-os/` is the ignored derived-artifact location.
- `candidates/formation_service.py`: `CandidateFormationService.form()` validates existing evidence IDs and persists a `CandidatePacket` through `CandidateRepository`.
- `tests/test_crawler_contract.py` and `tests/test_candidate_formation_boundary.py`: existing conventions use `unittest`, isolated `.opportunity-os/*.db` files, and injected/local acquisition inputs.
- Fact interfaces remain downstream and untouched: `opportunity/evaluation/contracts.py` and the Fact Production Boundary consume ledger evidence only after candidate formation.

## Files created

- `adapters/roblox.py`
- `tests/test_phase_18_18_1_roblox_input_layer.py`
- `docs/phase-18.18.1-roblox-input-layer.md`

## Files modified

- `adapters/__init__.py`

## Verification

- `python -m unittest tests.test_phase_18_18_1_roblox_input_layer -v` — 3 passed
- `python -m unittest discover -s tests` — 210 passed

Evidence level: `RUNTIME_VERIFIED`

## Problems discovered

- `CandidatePacket` currently requires a `confidence` value even for a purely evidentiary candidate. This phase uses the existing neutral `0.5` requirement and does not interpret it as an opportunity judgement. The field is a contract friction point for a later, separately authorized review.
- `EvidenceObject.raw_reference` can store the raw captured observation and hash it, while source locator, acquisition method, provenance, and measurement context correctly fit its existing `metadata`. No contract expansion was needed.



