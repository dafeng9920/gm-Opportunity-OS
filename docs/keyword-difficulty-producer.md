# Keyword Difficulty Fact Producer v0.1

`keyword-difficulty-producer@0.1` produces only `keyword_difficulty@0.1`. It does not call a keyword-difficulty API, crawl a search engine, decide whether an opportunity is worthwhile, or create an Accepted Fact.

It accepts exactly one persisted SERP Evidence reference with a structured `keyword_difficulty_measurement`. That Measurement contains its original `source_reference`, query, ordered ranked-result observations, and the fixed `mean_result_competition_score_v1` calculation rule. Each observation carries a position, domain, and 0–100 observed competition score.

The Producer deterministically calculates the Fact value as the rounded arithmetic mean of at least three ranked-result competition scores. A source-provided score is Evidence input, not system truth: the final Fact remains reproducible from the stored observations, source reference, and calculation rule.

The existing Fact Quality Policy must require `source_reference`, `query`, `ranked_results`, `calculation_rule`, and `calculated_score`, together with standard fact provenance (`query`, `source`, `method`, `captured_at`). Only the resulting Accepted Fact may be supplied to the Competition Gate.