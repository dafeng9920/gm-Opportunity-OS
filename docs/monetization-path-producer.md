# Monetization Path Fact Producer v0.1

`monetization-path-producer@0.1` produces only `monetization_path@0.1`. It does not estimate revenue, decide that an opportunity is profitable, generate a commercial strategy, or create an Accepted Fact.

The v0.1 Fact value is exactly one controlled path: `AFFILIATE`, `DIGITAL_PRODUCT`, `SAAS`, `SERVICE`, `ADS`, or `MARKETPLACE`. Evidence must contain a structured `monetization_path_measurement` with the original `source_reference`, the controlled path, a matching controlled evidence kind, the fixed `recognized_monetization_path_v1` rule, and the same declared result.

`UNKNOWN` is defined by the contract but is deliberately not producible as a Fact: a non-empty `UNKNOWN` string would incorrectly satisfy the current Monetization Gate. Unknown therefore means no Accepted Monetization Fact, which leaves the Gate `UNKNOWN`.

The v0.1 producer emits one evidenced controlled path per Fact. It does not aggregate multiple path claims; that would require a new versioned Gate Fact contract. The Quality Policy requires `source_reference`, `path`, `evidence_kind`, `validation_rule`, and `calculated_path`, plus standard monetization provenance (`path_scope`, `source`, `method`, `captured_at`).