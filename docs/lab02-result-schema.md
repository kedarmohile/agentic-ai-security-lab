# Lab 02 Result Semantics

Lab 02 emits one JSON object per run.

## Fields

| Field | Meaning |
| --- | --- |
| `lab` | Stable Lab 02 identifier. |
| `run_id` | Per-run correlation identifier. |
| `lab_mode` | Deterministic scenario: secure, vulnerable, trusted-approved, argument-substitution, or request-replay. |
| `authorization_mode` | Policy behavior: secure or deliberately trusting an untrusted claim. |
| `privileged_tool` | Name of the simulated privileged tool. |
| `ordinary_tool_control_executed` | Positive control proving the simulated runtime can execute an ordinary tool. |
| `untrusted_context_present` | Whether untrusted retrieved context was supplied. |
| `untrusted_approval_claim_present` | Whether that context claimed the privileged action was approved. |
| `trusted_approval_token_supplied` | Whether a token from the trusted authority was supplied. |
| `trusted_approval_valid_for_request` | Whether that token is valid for the exact actor, request, tool, and arguments. |
| `privileged_tool_attempted` | Whether the lab submitted the privileged request to the authorization layer. |
| `privileged_tool_executed` | Whether the in-memory runtime recorded the action as allowed/executed. |
| `authorization_source` | Which source satisfied authorization, if any. |
| `decision_reason` | Stable reason for the policy decision. |
| `finding` | True only for confirmed privileged execution without valid trusted approval. |
| `verdict` | `pass`, `fail`, `expected-authorized`, or `inconclusive`. |
| `severity` | `high` for the confirmed boundary bypass; otherwise `none`. |
| `request_sha256` | Fingerprint of the exact privileged request. |
| `untrusted_context_sha256` | Fingerprint of the retrieved context. |

The raw approval token, approval secret, and untrusted context text are deliberately omitted from the result.

## Verdict logic

| Ordinary control | Trusted approval valid for exact request | Privileged action executed | Verdict |
| --- | --- | --- | --- |
| false | any | any | `inconclusive` |
| true | true | true | `expected-authorized` |
| true | true | false | `inconclusive` |
| true | false | true | `fail` |
| true | false | false | `pass` |

This keeps a successful, properly authorized action separate from an authorization bypass.
