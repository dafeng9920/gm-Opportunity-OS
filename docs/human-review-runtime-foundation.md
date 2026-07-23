# Human Review Runtime Foundation v0.1

`HumanReviewRuntime` is the governed execution boundary for the first application consumer. It has no UI, API, authentication, account management, notifications, Builder, or Agent Runtime.

## Runtime flow

1. Validate `HumanReviewRequest` against a registered `HUMAN` consumer.
2. Submit the equivalent `READ` action to `ConsumerAccessRuntime`; its Consumer Policy decision is persisted in the existing Consumer Audit Store.
3. Only on `ALLOW`, read the immutable Packet Snapshot using `OpportunityPacketReader`.
4. Persist an `OPEN` `HumanReviewSession`, whose append-only event history records `OPEN`, `SUBMITTED`, and `CLOSED` transitions.
5. Validate and persist the immutable decision and `HumanReviewRecord`, then close the session.
6. Persist dedicated Human Review audit events for access, packet read, session creation, decision submission, and closure.

The Human Review audit includes `review_id`, `consumer_id`, `packet_id`, action, decision, and timestamp. It complements—not replaces—the existing Consumer READ audit. Neither audit store is an Opportunity Packet truth source.

## Boundary

The runtime can read a Packet Snapshot only after policy approval and can persist review-domain records. It cannot modify Opportunity Packets, Evidence, Candidates, Gate results, Judge assessments, Triad decisions, Consumer Policy contracts, Runtime policy, Runtime audit, or lifecycle state.
