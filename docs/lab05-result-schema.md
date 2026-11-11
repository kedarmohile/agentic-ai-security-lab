# Lab 05 Result Semantics

Lab 05 emits one JSON object per run.

## Fields

| Field | Meaning |
| --- | --- |
| `lab` | Stable Lab 05 identifier. |
| `run_id` | Per-run correlation identifier. |
| `lab_mode` | Deterministic scenario being exercised. |
| `verifier_mode` | Strict identity/scope validation or deliberately vulnerable bearer-scope validation. |
| `owner_control_succeeded` | Parent credential worked for the intended Agent A request. |
| `parent_credential_exposed_to_child` | The exact raw parent token crossed into Agent B's context. |
| `child_received_credential` | Agent B received any credential. |
| `child_credential_is_parent_token` | Child credential is byte-for-byte the same parent token. |
| `credential_exactly_valid_for_child_request` | Credential matches child subject, audience, action, resource, and request. |
| `child_action_attempted` | Lab submitted the synthetic child service request. |
| `child_action_executed` | In-memory service recorded the child action as allowed. |
| `decision_reason` | Stable service authorization reason. |
| `exposure_finding` | Raw parent credential crossed the agent boundary. |
| `unauthorized_use_finding` | Child action executed with a credential not valid for the exact child request. |
| `finding` | Overall security finding. |
| `verdict` | pass, fail, expected-authorized, or inconclusive. |
| `severity` | none, medium, or high. |
| `request_sha256` | Fingerprint of the exact child service request. |
| `child_credential_sha256` | Fingerprint of child credential, or null when none was propagated. |
| `parent_credential_sha256` | Fingerprint of the parent credential. |

## Severity model

| Condition | Verdict | Severity |
| --- | --- | --- |
| Owner control fails | inconclusive | none |
| Parent credential leaks but strict verifier blocks child | fail | medium |
| Invalid-for-child credential executes | fail | high |
| Distinct derived child credential executes within exact scope | expected-authorized | none |
| No leak and no unauthorized action | pass | none |
