# Real Signal Source Layer v0.1

The first real collector is a deliberately narrow YouTube public-channel RSS adapter.

```
Public YouTube channel RSS -> Scrapling isolated runtime -> YouTube RSS Signal Adapter -> crawler.v0 -> Evidence Ledger
```

Allowed: HTTPS to `www.youtube.com/feeds/videos.xml`, one supplied channel id, local title query filtering, and a local ISO date window. Forbidden: YouTube search, login, cookies, browser automation, API credentials, bulk scheduling, and direct Core access.

The Runtime Manager permits only the `www.youtube.com` host and records runtime id, adapter id, Scrapling version, hashes, timing, and decision in the existing audit log.
