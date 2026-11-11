# Lab 04 Result Semantics

Lab 04 emits one JSON object per run.

## Fields

| Field | Meaning |
| --- | --- |
| `lab` | Stable Lab 04 identifier. |
| `run_id` | Per-run correlation identifier. |
| `lab_mode` | secure, vulnerable, exact-delegated, resource-substitution, delegate-substitution, or request-replay. |
| `broker_mode` | secure delegation checking or deliberately vulnerable deputy-privilege trust. |
| `principal_id` | Original synthetic principal. |
| `delegate_id` | Agent receiving delegated authority. |
| `deputy_id` | More-privileged downstream agent asked to act. |
| `requested_action` | Action requested from the deputy. |
| `requested_resource` | Resource targeted by the request. |
| `control_delegation_succeeded` | Positive control proving an exact delegation can traverse the chain. |
| `deputy_has_local_capability` | Whether the deputy itself is technically permitted to perform the action. |
| `delegation_token_supplied` | Whether a trusted grant token was supplied. |
| `delegation_valid_for_request` | Whether that grant matches the exact chain and request. |
| `delegated_action_attempted` | Whether the test submitted the action to the broker. |
| `delegated_action_executed` | Whether the in-memory runtime recorded the action as allowed. |
| `authorization_source` | Delegation grant, deputy local privilege, or none. |
| `decision_reason` | Stable policy reason. |
| `finding` | True only for execution outside the original principal's valid delegation. |
| `verdict` | pass, fail, expected-authorized, or inconclusive. |
| `severity` | high for confirmed confused-deputy execution; otherwise none. |
| `request_sha256` | Fingerprint of the exact delegated action. |
| `delegation_token_sha256` | Fingerprint of the grant token; raw token omitted. |

## Verdict logic

| Control works | Deputy locally capable | Delegation valid | Action executes | Verdict |
| --- | --- | --- | --- | --- |
| false | any | any | any | `inconclusive` |
| true | false | any | any | `inconclusive` |
| true | true | true | true | `expected-authorized` |
| true | true | true | false | `inconclusive` |
| true | true | false | true | `fail` |
| true | true | false | false | `pass` |
