# Dependency report ¡ª Hermes Agent

- Installation declared upstream: managed installer or `uv pip install -e ".[all,dev]"`.
- Observed dependency surface: Python agent runtime plus optional Node/web UI, Docker, gateway/channel providers, MCP/tool integrations, browser/terminal backends.
- System/environment: Python 3.12.10 on Windows; no venv, package, Node dependency, service, credential, or installer created.
- Verdict: dependency graph is intentionally not acceptable in Core; any future adapter must isolate a pinned runtime and expose a small RPC/result boundary.
