# Intelligence Signal Layer v0.1

This layer defines what Opportunity OS may observe. A source catalogue is not a collection permit, and a signal is not an opportunity.

```
SignalRecord -> DiscoveryRecord (crawler.v0) -> EvidenceObject -> CandidatePacket -> Triad Gate
```

`SignalEvidenceMapper` only creates a `DiscoveryRecord`. Existing `CrawlerContractRunner` remains the sole writer into the Evidence Ledger. No path here creates a Candidate Packet or a governance decision.

| Source | Type | Status | v0.1 behaviour |
| --- | --- | --- | --- |
| SteamDB | Reference | REFERENCE_ONLY | Registered for reference only |
| IGDB | API | RESERVED | No API client or credentials |
| YouTube | Signal | PLANNED | Contract only; no collection implementation |
| Roblox Official | Data Source | PLANNED | Reserved for the future plugin |

## YouTube contract

Input: `YouTubeSignalRequest(query, channel, time_window)`.

Future output: a tuple of `VideoSignal`; every item requires source `youtube`, type `video`, video id, original evidence reference, timestamp, and bounded confidence. The protocol deliberately includes no HTTP, browser, login, cookie, or scraping implementation.
