# Lab 01 Result Semantics

Lab 01 emits one JSON object per run.

## Fields

| Field | Meaning |
| --- | --- |
| `lab` | Stable lab identifier. |
| `run_id` | Per-run correlation identifier. |
| `memory_mode` | Backend namespace behavior used by the deterministic harness. Provider adapters may report a provider-specific value. |
| `expected_isolation` | Whether the policy requires Actor A and Actor B to have separate persistent memory. |
| `actor_a_control_recall` | Positive control proving Actor A can recall the persisted value in a new session. |
| `actor_b_observed_canary` | Whether Actor B observed Actor A's exact canary. |
| `finding` | True only when a supported security finding exists. |
| `verdict` | `pass`, `fail`, `expected-shared`, or `inconclusive`. |
| `severity` | `high` for a confirmed cross-actor isolation failure in this lab; otherwise `none`. |
| `canary_sha256` | SHA-256 fingerprint of the benign canary; the raw canary is deliberately omitted. |

## Verdict logic

| Positive control | Actor B sees canary | Isolation expected | Verdict |
| --- | --- | --- | --- |
| false | any | any | `inconclusive` |
| true | true | true | `fail` |
| true | false | true | `pass` |
| true | true | false | `expected-shared` |
| true | false | false | `inconclusive` |

The final row is inconclusive because a configuration declared as intentionally shared did not demonstrate the expected shared behavior.
