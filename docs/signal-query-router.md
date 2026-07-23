# Signal Query and Router v0.1

`SignalQuery` records a person's intent as data. `SignalRouter` reads only registered active source capabilities and returns `CollectorExecutionPlan` records. It never executes an adapter, writes Evidence, creates Candidates, calls a Judge, calls Triad, or changes Gate rules.

Current capability: `youtube-rss` supports `video_signal` through `adapter.youtube-signal`; it is limited to supplied public channel IDs, RSS, and local filtering. No domain name is interpreted by the router.

## Query path

```
SignalQuery -> SignalRouter -> CollectorExecutionPlan -> adapter-specific request translator -> SignalRecord -> DiscoveryRecord -> Evidence Ledger
```

The final three steps remain the existing controlled acquisition path. The generated Mermaid files are derived, ignored by Git, and regenerated from fact registries.
