# Consumer Contract Foundation v0.1

A Consumer is an identity that may eventually consume an Opportunity Packet. It is neither a Skill nor a Runtime.

v0.1 provides immutable identity, capability, read-request, and audit-event contracts plus a dedicated registry and validator. The sole declared action is `READ`. No module here resolves, queries, alters, exports, delivers, or executes a Packet.

Future Consumer Layer work must put policy and audit checks before any Packet Store read. It must not reuse Runtime Invocation contracts or the Runtime Audit event schema.
