# Human Review Consumer Boundary Contract v0.1

`Human Review` is the first application-level consumer boundary. It consumes an immutable Opportunity Packet reference and produces an immutable review record. It is not a decision engine and does not change the packet lifecycle.

## Contracts

`HumanReviewRequest` identifies a registered `HUMAN` consumer, a `PacketReference`, and the packet-contract version. `HumanReviewDecision` records exactly one of `APPROVE`, `REJECT`, or `REQUEST_MORE_EVIDENCE`, with a bounded non-empty reason. `HumanReviewRecord` joins the validated request and decision as review evidence.

The review contract version must equal the referenced packet version. The requested consumer must be registered as `HUMAN`, and that same consumer must supply the decision. These checks use `ConsumerRegistry` only; this layer does not read a packet or call the Consumer Policy Gate.

## Boundary

Human Review can read a Packet Snapshot through the already governed Consumer read path and can create an in-memory `HumanReviewRecord` after contract validation. It cannot modify an Opportunity Packet, Evidence, Candidate, Gate result, Judge assessment, Triad decision, Runtime policy, or any lifecycle state.

This phase includes no UI, API, authentication, user management, workflow engine, record persistence, Builder, or Agent Runtime. Those require later, separately governed phases.
