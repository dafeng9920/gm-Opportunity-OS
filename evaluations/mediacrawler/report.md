# MediaCrawler evaluation ¡ª v0.1

## Evidence and pin
- Source: https://github.com/NanmiCoder/MediaCrawler
- Fixed source snapshot: `0625e01a6bc717a3fc9c96d3dac7fb8957043838` (no upstream tag returned).
- License: **NON-COMMERCIAL LEARNING LICENSE 1.1**.
- `git ls-remote origin HEAD` verified the commit. The isolated shallow clone was stopped before checkout after timeout; no code or installer ran. See `source-lock.json`.

## Dependencies and environment
Python project with platform-specific, browser/login-oriented collection. No dependencies, browsers, accounts, or external services were installed/configured.

## Capability assessment
Upstream advertises collection of Xiaohongshu, Douyin, Kuaishou, Bilibili, Weibo, Baidu Tieba, and Zhihu posts/comments. A separately licensed adapter could theoretically map raw outputs to `DiscoveryRecord`; it does not provide the Opportunity OS contract directly.

## Security and compliance review
Upstream requires target-platform terms and `robots.txt` compliance, prohibits large-scale crawling/disruption, and restricts use to non-commercial learning/research. Login/session, anti-bot, privacy, account, and platform-risk boundaries require independent review.

## Opportunity OS contract fit
Technical fit cannot overcome the upstream commercial-use prohibition. A wrapper cannot remove licensing or platform-compliance restrictions.

## Decision
**REJECT.** Licensing and compliance veto. No component was registered, activated, installed, or integrated.
