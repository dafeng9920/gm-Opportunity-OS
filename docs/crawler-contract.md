# Crawler Layer Contract v0.1

The crawler layer is an acquisition boundary, not a business layer. It contains no Roblox, SEO, ranking, candidate, agent, or publishing logic.

## Input

`CrawlRequest` is supplied by Core or an orchestrator. It has a source label, opaque target, structured parameters, request ID, and request timestamp. The contract does not prescribe URLs, queries, credentials, pagination, or crawler libraries.

## Output

An adapter implementing `CrawlerPort` returns `DiscoveryRecord` values. A record must retain `external_id`, source identity, source type, capture time, and `raw_reference`. It may add structured metadata, but cannot replace the raw reference with an AI summary.

## Core boundary

`CrawlerContractRunner` is the only v0.1 bridge into Core. It requires an active `crawler` component in the Component Registry and writes one `EvidenceObject` per discovery to the Evidence Ledger. The resulting evidence metadata records the crawler ID, crawl request ID, and external ID for traceability.

The adapter never writes the Evidence Ledger itself and never creates Candidate Packets. This keeps external acquisition replaceable and Core ownership explicit.
