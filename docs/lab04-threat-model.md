# Lab 04 Threat Model — Confused-Deputy Delegation

## Security property

A privileged deputy may execute an action only when the **original principal's delegation** authorizes the exact principal, delegate, deputy, request, action, and resource.

The deputy's own privilege is necessary to perform an action, but it is not sufficient evidence that the original principal authorized that action.

## Delegation chain

Lab 04 models:

```text
principal-alice
      │ delegates narrow authority
      ▼
   agent-a
      │ requests help
      ▼
   agent-b  ← more-privileged deputy
      │
      ▼
simulated action ledger
```

The confused-deputy failure occurs when Agent B uses its own broader capability on behalf of Agent A even though the principal never delegated that broader authority.

## Why this is different from Lab 02

Lab 02 asks:

> Is this privileged tool call approved?

Lab 04 asks:

> Did the original principal actually delegate this authority through the agent chain?

A system can have a strong tool-level authorization gate and still mishandle delegation if a privileged downstream agent interprets its own permissions as authority to act for an upstream principal.

## Delegation binding

The deterministic lab uses an HMAC grant bound to:

- principal identity;
- delegate identity;
- deputy identity;
- request identifier;
- action;
- resource.

Changing any one dimension invalidates the grant.

HMAC is only the lab's compact deterministic mechanism. A production design could use signed capabilities, workload identity plus policy, OAuth token exchange, a policy engine, or another trusted delegation mechanism.

## Local deputy capability

Agent B has local capability to:

- read `report/Q4`;
- publish `report/Q4`;
- publish `report/executive`.

That broad local privilege is intentional. The lab needs the deputy to be technically capable of the action so the result measures the **delegation boundary**, not a lack of local permission.

## Controls and scenarios

### Exact delegated control

The principal grants Agent A permission to read `report/Q4`, and Agent B executes that exact delegated read.

This positive control proves the delegation chain is operational.

### Secure scope-escalation denial

The principal delegates **read** on `report/Q4`, but Agent A asks Agent B to **publish** it.

Agent B can publish locally, but the secure broker denies because the principal's grant does not authorize publish.

### Deliberately vulnerable confused deputy

The same narrow read grant is used, but the vulnerable broker treats Agent B's local publish capability as sufficient authority.

The simulated publish executes and Lab 04 emits a finding.

### Exact delegated publish

The principal explicitly delegates publish for the exact request. Secure execution is expected and is not a finding.

### Resource substitution

A publish grant for `report/Q4` is presented for `report/executive`. Secure behavior is denial.

### Delegate substitution

A grant to `agent-a` is presented by `agent-c`. Secure behavior is denial.

### Request replay

A grant for `request-previous` is replayed for `request-001`. Secure behavior is denial.

## Finding logic

A high-severity finding is emitted only when:

- the exact-delegation control succeeds;
- the deputy has the local capability to perform the requested action;
- the supplied delegation is invalid for the exact request;
- the delegated action nevertheless executes.

This isolates confused-deputy behavior from ordinary permission failures.

## Safety

Lab 04 has no real privileged effects.

"Execution" means only that the `DelegatedAction` object was appended to an in-memory list. The lab does not:

- call an external API;
- access a cloud account;
- invoke a shell;
- modify a file or database;
- contact a network endpoint;
- act on a real report or resource.

All identities and resources are synthetic.

## Evidence minimization

The raw delegation token and signing secret are never included in result evidence. The result stores SHA-256 fingerprints for the exact request and delegation token.

The synthetic principal, agent, action, and resource identifiers remain visible because they explain the delegation path under test.

## Out of scope

Lab 04 does not currently test:

- real identity-provider token exchange;
- OAuth/OIDC implementation details;
- temporal expiry;
- revocation;
- multi-party approval;
- recursive delegation depth greater than one deputy;
- real tool execution;
- malicious code or sandbox escape.

Those can be layered on without changing the core invariant.
