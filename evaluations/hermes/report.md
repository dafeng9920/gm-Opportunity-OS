# Hermes Agent evaluation ¡ª v0.1

## Evidence and pin
- Source: https://github.com/NousResearch/hermes-agent
- Fixed release: `v2026.7.20`; commit `3ef6bbd201263d354fd83ec55b3c306ded2eb72a`.
- License: MIT. Tag was resolved with `git ls-remote --tags`; the isolated shallow clone was stopped before checkout after exceeding the evaluation window. No installer, dependency resolver, or Hermes code was run. See `source-lock.json`.

## Dependencies and environment
Upstream documents a managed installer and editable `.[all,dev]` install using `uv`; the project includes Python, Node, Docker, web, gateway, and tool surfaces. This is not a Core dependency. Evaluation environment: Windows, Python 3.12.10, no Hermes venv or installed package.

## Capability assessment
Upstream documents task execution, terminal/browser tool calling, memory/skills, scheduling, subagent delegation, and multiple execution backends. It meets the profile of an agent execution candidate.

## Security review
Hermes describes itself as single-tenant; its default terminal backend runs commands directly on the host. Terminal, file, browser, messaging, MCP, credential, network, and configuration surfaces make untrusted prompt/tool output unsafe to grant authority over Opportunity OS state.

## Opportunity OS contract fit
A future adapter may submit explicit bounded tasks and validate structured results. Hermes must not receive SQLite write access, Registry administration, autonomous candidate acceptance, production credentials, or commercial-decision authority. Required controls: isolated backend, capability allowlist, read-only evidence inputs, and Core-owned handoff.

## Decision
**ADAPT.** Relevant capability, but direct adoption violates least privilege and Core ownership. No registration or integration occurred.
