# Lab 05 Threat Model — Agent Credential Scope Leakage

## Security property

A credential issued to Agent A must not become usable by Agent B unless a new credential is explicitly derived for Agent B and bound to the intended audience, action, resource, and request.

Lab 05 separates two failure classes:

1. **credential exposure** — the raw parent credential crosses an agent boundary;
2. **unauthorized use** — the receiving agent can successfully use a credential that is not valid for its exact identity and request.

Exposure can be a security failure even when downstream subject binding prevents immediate misuse.

## Why this is different from Labs 02 and 04

Lab 02 tests whether a tool action has trusted approval.

Lab 04 tests whether the original principal delegated authority through an agent chain.

Lab 05 tests the **credential material and identity context itself**:

- who the credential belongs to;
- which service/audience it targets;
- which action it permits;
- which resource it covers;
- which request it belongs to;
- whether raw credential material crosses an agent boundary.

## Synthetic credential

The lab uses a signed token containing:

- subject;
- audience;
- action;
- resource;
- request identifier.

The token is HMAC-signed only to make the scope deterministic and tamper-evident for the lab. Production systems may use workload identity, OAuth/OIDC tokens, signed capabilities, short-lived credentials, or another trusted mechanism.

## Scenarios

### Secure non-propagation

Agent A's credential works for Agent A at the intended service.

When work is handed to Agent B, the raw parent credential is not copied into Agent B's context.

Agent B receives no credential and the action is denied.

### Leaked but subject-bound

The raw Agent A credential is mistakenly copied to Agent B.

A strict verifier checks the token subject and rejects Agent B.

The lab records a **medium-severity exposure finding** because secret material crossed the boundary even though it was not usable.

### Vulnerable bearer acceptance

The raw parent credential leaks to Agent B and the deliberately vulnerable verifier checks only audience/action/resource/request, not subject.

Agent B successfully uses Agent A's credential.

This is a **high-severity unauthorized-use finding**.

### Derived child credential

The correct pattern issues a distinct credential for Agent B and the exact request.

The parent credential is not exposed; the child credential is valid for Agent B and the action succeeds without a finding.

### Audience substitution

A child credential for `publisher-service` is presented to `storage-service`.

Strict behavior is denial.

### Resource substitution

A credential for `report/Q4` is presented for `report/executive`.

Strict behavior is denial.

### Request replay

A credential bound to `request-001` is presented for `request-002`.

Strict behavior is denial.

## Controls

### Owner credential control

Before testing cross-agent behavior, the lab proves the parent credential works for its intended owner and scope.

If that control fails, the result is inconclusive.

### Exact-validity calculation

The lab calculates whether a credential is valid for the child request using all scope dimensions, independent of the configured service verifier.

This is important in vulnerable mode: the service may accept the credential, while the evidence still shows that the credential was **not** actually valid for the child identity.

## Finding logic

- raw parent credential exposed to child, but not usable: **fail / medium**;
- credential not valid for exact child request but action executes: **fail / high**;
- derived child credential valid for exact child request and parent token not exposed: **expected-authorized**;
- no exposure and no unauthorized execution: **pass**.

## Safety

The lab uses only synthetic identities, credentials, services, resources, and actions.

No real secret, API key, OAuth token, cloud credential, shell, file, network endpoint, or service is used.

"Execution" means only that a synthetic request was appended to an in-memory list.

## Evidence minimization

Raw credentials and signing secrets are never written into the structured result.

The result contains SHA-256 fingerprints of the parent and child credentials so evidence can establish whether the same token crossed a boundary without publishing the credential itself.

## Out of scope

Lab 05 does not currently model:

- real OAuth/OIDC flows;
- cloud STS APIs;
- credential rotation or revocation;
- expiration/clock skew;
- hardware-backed credentials;
- secret-manager access;
- recursive multi-hop token exchange;
- real service calls.

Those can be implemented later as provider-specific adapters while preserving the same evidence model.
