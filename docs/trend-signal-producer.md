# Trend Signal Fact Producer v0.1

`trend-signal-producer@0.1` produces only `trend_up@0.1`. It never fetches data, calls an Agent, or interprets commercial value.

It accepts exactly one persisted Evidence reference whose metadata contains a structured `trend_measurement`: the exact `source_reference`, a two-point-or-more `time_window`, numeric `observations`, and the fixed `latest_gt_earliest` comparison rule. The source reference must equal the Evidence object's original `raw_reference`.

The calculated result is `true` only when the final observation is strictly greater than the initial observation; a flat or declining series is `false`. If no accepted trend fact exists, the existing Demand Gate remains `UNKNOWN`; no textual trend summary becomes a Fact.

The producer supplies a Measurement Artifact to the existing Fact Production Boundary. Its Quality Policy must require the Measurement fields `source_reference`, `time_window`, `observations`, `comparison_rule`, and `calculated_direction`, plus the standard trend provenance (`query`, `region`, `time_window`, `source`, `method`, `captured_at`).