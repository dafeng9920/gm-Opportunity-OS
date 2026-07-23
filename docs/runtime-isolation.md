# Runtime Isolation Layer v0.1

## Boundary

`Adapter -> RuntimeManager -> MockSandbox -> external-worker seam -> Contract -> Core` is mandatory for runtime-mediated calls. The worker seam receives no Core object or database path. `MockSandbox` deliberately launches no process in v0.1.

## Runtime Registry

A runtime requires both `Component(type="runtime", status="active")` and `RuntimeRegistration(status="available")`. The registration records name, runtime type, version, and policy. `RuntimeManager` rejects anything else before handler invocation.

## Enforced restricted-v0

- temporary workspace: read-only only
- network: none
- execution: controlled mock callback only
- Core database, Registry, and secrets: forbidden

## Audit

Every invocation emits a SQLite `runtime_audit` event: caller, adapter, runtime, input hash, output hash, timestamp, and `ALLOW`, `DENY`, or `ERROR`. Denied attempts are audited without running the handler.

## Non-goals

This phase contains no real subprocess/container launch, browser binary, Hermes installation, Scrapling package, network request, secret mount, or production permission. A later runtime implementation must preserve these interfaces and make the policy enforcement OS/container-real.
