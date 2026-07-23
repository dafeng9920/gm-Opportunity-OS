# Evidence-backed Candidate Formation Boundary v0.1

`CandidateFormationService` is the production boundary from Evidence Ledger references to a persisted `CandidatePacket`.

```text
Human selects Evidence IDs
↓
EvidenceReferenceValidator
↓
CandidateFormationService
↓
CandidateRepository
```

The service receives an immutable `CandidateFormationRequest`. It verifies that every supplied ID exists through the Evidence Ledger lookup and that every referenced Evidence record has a source, capture time, and content hash. It then persists one `CandidatePacket` whose `evidence_ids` exactly match the verified IDs.

The supported-domain list is supplied by the caller. The shared boundary therefore does not hard-code Roblox or any other business domain.

This boundary makes no collection call and has no dependency on Gates, Judge, Triad, Opportunity Packet assembly, Consumer layers, Skills, Builder, or Runtime policy. It only establishes that an object is evidence-backed enough to enter later evaluation; it does not decide opportunity value.

Existing direct `CandidatePacket` construction remains available for fixtures and legacy internal contracts. Production candidate formation must use this service.
