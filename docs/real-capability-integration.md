# Real Capability Integration v0.1

## Scrapling experimental integration: verified

A real `scrapling[fetchers]==0.4.11` installation lives only in `.opportunity-os/venvs/scrapling` and is Git-ignored. The Core never imports it. `runtime.scrapling-venv` launches `runtime/scrapling_worker.py` as that venv's subprocess. The worker has no Core imports and only permits one unauthenticated `https://example.com` fetch.

The verified call followed: `runtime.scrapling-venv -> SandboxedFetchBackend -> ScraplingAdapter -> CrawlerContractRunner -> EvidenceLedger`. It produced an ALLOW audit event with version, duration and hashes. See `integrations/evidence/phase6-scrapling.json`. No login, Cookie, browser binary, dynamic automation, proxy, or multi-page crawling was used.

## Hermes experimental integration: blocked

Hermes is not installed or started. This host has no configured supported model provider credential and no Docker/Podman/other OS-level whole-process runtime. Hermes' own security policy identifies OS-level isolation as the containment boundary; a project-local Python venv would not meet the required safety claim. A real Hermes task/tool/structured-result run therefore remains blocked pending a user-provided model endpoint/credential and approved OS-level sandbox runtime.

## Admission state

Scrapling is used only as a pinned experimental backend behind the existing Adapter/Runtime/Contract boundary. Hermes remains evaluated `ADAPT`, but inactive as a real runtime. MediaCrawler remains `REJECTED` and is absent from this phase.
