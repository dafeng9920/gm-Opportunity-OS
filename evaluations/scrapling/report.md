# Scrapling evaluation ¡ª v0.1

## Evidence and pin
- Source: https://github.com/D4Vinci/Scrapling
- Fixed release: `v0.4.11`; commit `aba2b3a57f3009cb6607dba58bb51863ca48d00d`.
- License: BSD-3-Clause.
- Tag and commit were resolved with `git ls-remote --tags`; no package, browser binary, fetcher extra, or remote fetch was executed. See `source-lock.json`.

## Dependencies and environment
Parser-only package targets Python 3.10+. Fetchers/CLI are optional extras. Browser-backed use requires `scrapling install`, which downloads browsers and system/fingerprint dependencies. Evaluation: Windows, Python 3.12.10; none installed.

## Capability assessment
Upstream documents HTML parsing, CSS/XPath, static requests, browser/dynamic fetchers, adaptive selector relocation, and optional shell/MCP features. It is a candidate backend, not a `CrawlerPort` implementation, and does not produce `DiscoveryRecord` directly.

## Security and compliance review
Network fetches, browser automation, stealth/fingerprinting, CDP connection, and browser-profile data enlarge the security/compliance surface. Site terms, robots.txt, privacy law, provenance checks, and isolated browser binaries are mandatory.

## Opportunity OS contract fit
A narrow future adapter can accept `CrawlRequest`, perform bounded retrieval, return `DiscoveryRecord`, and leave Evidence writes to the existing Core runner. It must prohibit direct Ledger/Registry access and enforce allowlists/rate limits; optional MCP/shell features remain disabled.

## Decision
**ADAPT.** BSD-3-Clause and generic collection fit, but direct adoption would bypass the Crawler Contract and add unnecessary surface to Core.
