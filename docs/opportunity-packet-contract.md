# Opportunity Packet Contract v0.1

An Opportunity Packet is the canonical immutable output snapshot after discovery and evaluation. It is assembled by system code from references to Evidence, Candidate, deterministic Gate Results, optional Judge Assessment, and Governance status.

Readers may include a future UI, API, Builder gate, Agent, and human reviewer. None may mutate a finalized version. A changed result requires a new `version` stored alongside the historical packet.

The Packet never copies Evidence content; it carries only evidence id, source, and timestamp. Judge explanation is separate from deterministic Gate results. Governance remains the permission authority: Packet `next_action` records the system-permitted next step and never triggers it.
