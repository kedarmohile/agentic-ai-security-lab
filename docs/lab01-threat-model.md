# Lab 01 Threat Model — Cross-Actor Persistent Memory Isolation

## Security property

Data written to persistent memory for one actor must not become visible to another actor unless the application explicitly defines the memory as shared.

The lab treats persistent memory as an **authorization boundary** rather than merely a convenience feature.

## Assets

Potentially sensitive state retained by an agentic application, including:

- user preferences;
- conversation summaries;
- task or workflow history;
- episodic memory;
- retrieved notes;
- identifiers or user-provided facts;
- state that can influence later agent behavior.

Lab 01 uses a synthetic canary instead of real sensitive data.

## Principals

- **Actor A** — writes the canary and is expected to retrieve it in a later session.
- **Actor B** — must not retrieve Actor A's canary when isolation is required.

Sessions are intentionally separate from actor identity. This prevents a test from confusing "new session" with "new principal."

## Failure modes modeled

The deterministic vulnerable backend represents classes of implementation defects such as:

- a shared namespace used where actor scoping was intended;
- an actor identifier omitted from a persistence key;
- a cache or lookup key that is insufficiently scoped;
- a routing/configuration error that maps multiple principals to one memory namespace.

The lab does **not** assert which implementation defect caused a real-world failure. It only evaluates the observable isolation property.

## Controls

### Positive persistence control

Actor A writes the canary in one session and reads it from another.

If this control fails, the result is **inconclusive**. A target that did not persist the canary cannot demonstrate whether cross-actor persistence is isolated.

### Cross-actor negative control

Actor B attempts to recall the same memory key.

When isolation is expected, observing Actor A's canary is a finding.

### Explicitly shared policy

Some applications intentionally share memory between principals. Lab 01 therefore separates observed sharing from policy.

When the configured policy says sharing is expected, a shared canary is reported as `expected-shared`, not as a vulnerability.

## Evidence minimization

The structured result does not store the raw canary. It stores a SHA-256 fingerprint so test artifacts can correlate the value without unnecessarily copying the value into downstream logs.

Provider-specific adapters should apply the same principle to real identifiers and sensitive values.

## Out of scope

Lab 01 does not currently test:

- prompt injection;
- memory poisoning;
- unauthorized writes;
- tool authorization;
- tenant breakout beyond the memory read boundary;
- semantic influence where the canary is not reproduced;
- provider-specific IAM configuration;
- exploitability of a named commercial service.

These can be added as separate labs or provider adapters without changing the core isolation invariant.

## Taxonomy note

This lab is primarily an **authorization and data-isolation** test. It is relevant to broader AI-security concerns around sensitive-information disclosure and agent memory, but this repository intentionally does not assign a formal MITRE ATLAS or OWASP technique identifier unless the mapping is precise and defensible.

## Relationship to public OSS discussions

- NVIDIA garak #2453 discusses a possible cross-actor memory-isolation probe.
- Elastic detection-rules #6722 proposes a behavioral detection for cross-actor use of AWS Bedrock AgentCore user-preference memory.

Those discussions motivated related engineering questions, but this lab is independently runnable and does not imply maintainer acceptance by either project.
