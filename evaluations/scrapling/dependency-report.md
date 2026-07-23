# Dependency report ¡ª Scrapling

- Parser-only base package: Python 3.10+; no fetcher/browser support in the base install.
- Optional surfaces: `[fetchers]`, `[ai]`, `[shell]`; browser-backed collection requires `scrapling install` to download browsers and system/fingerprint dependencies.
- System/environment: Python 3.12.10 on Windows; no package, optional extra, browser binary, or service installed.
- Verdict: only the parser/fetcher capability necessary for a future adapter should be considered, and only in a separate pinned environment.
