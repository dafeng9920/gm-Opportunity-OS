# Hermes static review ¡ª v2026.7.20

## Acquisition
Official source archive is isolated at `evaluations/hermes/source/hermes-agent-v2026.7.20.zip` and extracted beside it. The source-lock records immutable tag, commit, acquisition time and SHA-256. Source is outside Core import paths. No Hermes file has been executed, installed, imported, or registered as active runtime. License file states MIT.

## Project structure
- CLI entries: `pyproject.toml` exposes `hermes` and `hermes-agent`, both mapped to `run_agent:main`.
- Agent entry: `run_agent.py` defines `AIAgent`; the `agent/` package contains initialization, runtime helpers, conversation loop, provider adapters and context handling.
- Tool system: `toolsets.py`, `tools/`, and optional MCP manifests define toolsets and external integrations.
- Runtime surfaces: CLI/TUI, gateway, terminal backends, browser facilities, MCP, Python/Node/web/desktop artifacts.

## Dependency and system surface
The pinned `pyproject.toml` lists Python dependencies including `httpx[socks]`, `requests`, provider SDKs and optional extras such as MCP. The project includes Node/package files, Dockerfile, browser tooling, messaging/gateway integrations and model-provider configuration. A future runtime needs a separately pinned Python environment, model endpoint, network policy and OS-level sandbox.

## Permission surface
Static inspection identifies filesystem/file tools, terminal/shell and subprocess paths, network clients, browser/CDP tooling, MCP/plugin loading, and credential persistence/provider code. These capabilities make direct Core execution unacceptable.

## Opportunity OS fit
Hermes can be a future `agent.v0` backend only through `HermesAgentAdapter -> RuntimeManager -> isolated runtime -> structured AgentResult`. It may receive a bounded task and evidence references and return validated output. It must not receive Registry, Evidence Ledger, Candidate Repository, Queue, State Machine, Core database path, secrets, or authority to decide/admit opportunities.

## Status
Registry component is intentionally `inactive`; lifecycle reaches `WAITING_RUNTIME`. This truthfully distinguishes acquired/reviewed source from a usable runtime.
