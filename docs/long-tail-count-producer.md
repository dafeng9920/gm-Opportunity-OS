# Long Tail Count Fact Producer v0.1

`long-tail-count-producer@0.1` produces only `long_tail_count@0.1`. It does not call a keyword API, crawl search results, ask an LLM whether a phrase is valuable, or create an Accepted Fact.

Its Evidence contains a structured `long_tail_measurement`: exact `source_reference`, `topic_scope`, candidate items, count rule, and a declared result. The source reference must equal the Evidence object's original `raw_reference`.

The sole v0.1 rule is `qualified_long_tail_v1`. It normalizes whitespace and case; a candidate qualifies only if it contains the contiguous normalized topic scope and has at least one additional modifier token. Duplicate normalized candidates are counted once. The declared result must exactly equal the deterministic count of qualified items, so a manual count cannot bypass the Measurement.

The existing Fact Quality Policy must require `topic_scope`, `source_reference`, `candidate_items`, `qualified_items`, `count_rule`, and `calculated_count`, plus standard content-fact provenance (`query_family`, `source`, `method`, `captured_at`). Only the resulting Accepted Fact may be supplied to the Content Expansion Gate.