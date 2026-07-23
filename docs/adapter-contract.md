# Adapter Layer Contract v0.1

## Boundary

`External backend -> Adapter -> Contract runner -> Core` is mandatory. Backends receive neither `ComponentRegistry`, `EvidenceLedger`, `CandidateRepository`, queue, database path, nor state-machine object. Only Core-owned runners persist Evidence or advance system work.

## Registry

An adapter has a `Component(type="adapter")` plus `AdapterRegistration`: adapter ID, backend identifier/version, permission profile, contract, and status. `CrawlerContractRunner` accepts an adapter only if both records are active and its contract is `crawler.v0`. `AgentContractRunner` requires `agent.v0`.

## Capability policy

The only v0.1 profile is `restricted-v0`: filesystem restricted, network restricted, execution controlled, database no direct access. A policy requesting database access is rejected at construction. Production process launch, credentials, browser binaries, network allowlists, and real external packages are intentionally outside this phase.

## Scrapling adapter

`ScraplingAdapter` accepts a minimal injected fetch backend and converts its returned raw page into `DiscoveryRecord`. It cannot write Evidence; the existing Core runner performs that write after registry/contract validation. No Scrapling package is imported or installed.

## Hermes adapter

`HermesAgentAdapter` accepts an injected isolated runtime interface. It submits `AgentTask` and only returns a validated `AgentResult` whose task ID and evidence references are bounded to the submitted task. It cannot update Core state, use Queue, or access a database. No Hermes process is started.

## Excluded backend

MediaCrawler remains **REJECTED** due to its evaluation-stage licensing/compliance decision and has no adapter, registration, backend identifier, or test fixture in this layer.
