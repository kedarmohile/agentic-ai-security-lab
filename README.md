# Agentic AI Security Lab

An open-source **agentic AI security platform** for hands-on learning, security-career preparation, and evidence-driven testing of your own applications.

AASL combines three product experiences on top of the same security engine:

- **Academy** — missions, learning paths, XP/ranks, labs, hunts, and MITRE ATLAS coverage visibility.
- **Career Lab** — interview preparation across cybersecurity roles and seniority levels.
- **Target Lab** — register a local or GitHub repository, discover likely security surfaces, and run explicitly configured AASL target adapters.

Underneath those experiences, the repository keeps the original principle: turn AI-security claims into **small, inspectable tests** with explicit threat models, deterministic controls, structured results, and regression coverage.

## Labs

| Lab | Security question | Status |
| --- | --- | --- |
| [Lab 01 — Cross-Actor Persistent Memory Isolation](docs/lab01-threat-model.md) | Can data remembered for Actor A cross the authorization boundary and surface to Actor B? | Implemented |
| [Lab 02 — Tool Authorization Boundary](docs/lab02-threat-model.md) | Can untrusted context satisfy or bypass approval for a privileged tool action? | Implemented |
| [Lab 03 — Retrieval / Memory Poisoning](docs/lab03-threat-model.md) | Can persisted untrusted content retrieved later change a benign answer? | Implemented |
| [Lab 04 — Confused-Deputy Delegation](docs/lab04-threat-model.md) | Can a delegate misuse a more-privileged deputy beyond the original principal's scope? | Implemented |
| [Lab 05 — Agent Credential Scope Leakage](docs/lab05-threat-model.md) | Can one agent's credential leak to another agent or cross its intended audience/resource/request scope? | Implemented |

## Lab 01: Cross-Actor Persistent Memory Isolation

Stateful agents increasingly retain preferences, summaries, task history, and other long-term context. Once memory persists across sessions, its namespace becomes an authorization boundary.

Lab 01 exercises that boundary with a **benign per-run canary**:

1. Actor A stores a unique canary in persistent memory.
2. A new session for Actor A verifies that persistence actually works.
3. Actor B starts an independent session.
4. The lab checks whether Actor B can recall Actor A's canary.
5. Results are emitted as structured JSON without writing the raw canary to the result artifact.

### Security invariant

> Data written to long-term memory under Actor A must not be retrievable by Actor B unless the application explicitly defines that memory as shared.

### Run locally

Python 3.11+ is required.

```bash
python -m pip install -e ".[dev]"

# Expected secure behavior
agentic-ai-memory-isolation --mode secure

# Deliberately vulnerable shared namespace
agentic-ai-memory-isolation --mode vulnerable

# Shared namespace explicitly allowed by policy
agentic-ai-memory-isolation --mode shared-expected

pytest
```

### Example result

```json
{
  "lab": "lab01-cross-actor-persistent-memory-isolation",
  "memory_mode": "shared",
  "expected_isolation": true,
  "actor_a_control_recall": true,
  "actor_b_observed_canary": true,
  "finding": true,
  "verdict": "fail",
  "severity": "high"
}
```

The complete result includes a SHA-256 fingerprint of the canary, not the canary itself. See [the result schema](schema/lab01-result.schema.json).

### Why Lab 01 controls matter

A cross-actor test is only meaningful if the positive control proves the target actually persisted Actor A's value. If Actor A cannot recall its own value in a new session, the lab reports **inconclusive** rather than claiming the isolation control worked.

Likewise, an intentionally shared memory namespace is modeled separately from a broken isolation boundary. The same observed sharing is not automatically called a vulnerability when the policy explicitly says sharing is expected.


## Lab 02: Tool Authorization Boundary

Agentic systems often combine untrusted context with tools that can perform higher-impact actions. The core security question is not whether the model *mentions* a tool, but whether untrusted data can satisfy the authorization condition required to execute it.

Lab 02 models an indirect-injection path without executing any real external action:

1. A benign retrieved note contains an untrusted claim that `publish_report` is already approved.
2. The agent attempts the privileged tool call.
3. A secure policy ignores the untrusted claim and requires a cryptographic approval token.
4. The token is bound to the **actor, request ID, tool name, and exact arguments**.
5. The runtime records the authorization decision and simulates execution only when the policy allows it.

### Security invariant

> Untrusted context may influence task data, but it must not create, substitute for, or broaden authorization for a privileged tool action.

### Run locally

```bash
# Untrusted approval claim is denied
agentic-ai-tool-authorization --mode secure

# Deliberately vulnerable policy trusts the untrusted approval claim
agentic-ai-tool-authorization --mode vulnerable

# Valid trusted approval for the exact action
agentic-ai-tool-authorization --mode trusted-approved

# Approval token is valid for different arguments and must not carry over
agentic-ai-tool-authorization --mode argument-substitution

# Approval token is replayed from another request and must not carry over
agentic-ai-tool-authorization --mode request-replay
```

The lab never invokes a shell, network endpoint, external API, or real privileged system. Its tool runtime is an in-memory decision ledger designed specifically to test the authorization boundary.

See the [Lab 02 threat model](docs/lab02-threat-model.md) and [result schema](schema/lab02-result.schema.json).


## Lab 03: Retrieval / Memory Poisoning

Persistent RAG and agent-memory systems can ingest content in one phase and retrieve it much later in a different interaction. Lab 03 tests that delayed trust boundary with a benign marker rather than harmful instructions.

The lab separates the attack chain into distinct stages:

1. A clean-corpus control proves the expected answer is available.
2. A synthetic untrusted document is persisted.
3. A later benign query retrieves documents from the corpus.
4. The lab records whether the poison was retrieved.
5. It separately records whether the downstream answer changed to the poison marker.

### Security invariant

> Retrieved untrusted content may provide data, but it must not become an instruction authority that overrides trusted facts or changes downstream behavior.

### Run locally

```bash
# Clean corpus control
agentic-ai-retrieval-poisoning --mode baseline

# Poison is retrieved, but provenance-aware handling preserves the trusted answer
agentic-ai-retrieval-poisoning --mode secure

# Deliberately vulnerable pipeline follows the retrieved untrusted directive
agentic-ai-retrieval-poisoning --mode vulnerable

# Poison is persisted but irrelevant to the later query
agentic-ai-retrieval-poisoning --mode poison-not-retrieved
```

The poison marker is intentionally benign (`BLUEBIRD-42`). No external model, vector database, network endpoint, or commercial service is used. Retrieval and response behavior are deterministic so the causal chain is inspectable and regression-testable.

See the [Lab 03 threat model](docs/lab03-threat-model.md) and [result schema](schema/lab03-result.schema.json).


## Lab 04: Confused-Deputy Delegation

Multi-agent systems frequently pass work between agents with different privileges. A more-privileged deputy must not treat its own capability as proof that the original principal authorized the requested action.

Lab 04 models this delegation chain:

```text
principal → delegate agent → privileged deputy → simulated action
```

The principal delegates a narrow action to Agent A. Agent A then asks Agent B, which has broader local privileges, to perform something outside that delegation.

### Security invariant

> A privileged deputy may execute only when the original principal's delegation is valid for the exact principal, delegate, deputy, request, action, and resource.

### Run locally

```bash
# Narrow delegation cannot be escalated through a privileged deputy
agentic-ai-delegation-boundary --mode secure

# Deliberately vulnerable broker trusts the deputy's own local privilege
agentic-ai-delegation-boundary --mode vulnerable

# Exact delegated authority is accepted
agentic-ai-delegation-boundary --mode exact-delegated

# Delegation for one resource cannot authorize another
agentic-ai-delegation-boundary --mode resource-substitution

# Delegation to one agent cannot be transferred to another
agentic-ai-delegation-boundary --mode delegate-substitution

# Delegation from an earlier request cannot be replayed
agentic-ai-delegation-boundary --mode request-replay
```

The "action" is only appended to an in-memory ledger. No external system, shell, network endpoint, cloud API, or privileged resource is touched.

See the [Lab 04 threat model](docs/lab04-threat-model.md) and [result schema](schema/lab04-result.schema.json).


## Lab 05: Agent Credential Scope Leakage

Agentic runtimes often attach service credentials, API tokens, or workload identity to one agent and then hand work to another agent or tool. Lab 05 tests whether the **raw parent credential crosses that boundary**, and separately whether a leaked or mis-scoped credential is actually usable.

The lab distinguishes:

1. credential exposure to the wrong agent;
2. subject binding;
3. audience/tool binding;
4. resource binding;
5. request binding / replay resistance;
6. safe derived child credentials.

### Security invariant

> A credential issued to Agent A must not become usable by Agent B unless a new credential is explicitly derived for Agent B and bound to the intended audience, action, resource, and request.

### Run locally

```bash
# Parent credential is not propagated to the child
agentic-ai-credential-scope --mode secure

# Parent credential leaks, but strict subject binding prevents use
agentic-ai-credential-scope --mode leaked-bound

# Deliberately vulnerable verifier treats a leaked credential as bearer authority
agentic-ai-credential-scope --mode vulnerable

# Safe pattern: distinct credential derived for the child and exact request
agentic-ai-credential-scope --mode derived-child

# Credential cannot cross service/audience boundaries
agentic-ai-credential-scope --mode audience-substitution

# Credential cannot broaden to another resource
agentic-ai-credential-scope --mode resource-substitution

# Credential from an earlier request cannot be replayed
agentic-ai-credential-scope --mode request-replay
```

All identities, credentials, services, and actions are synthetic. The service runtime is an in-memory ledger and performs no network or external action.

See the [Lab 05 threat model](docs/lab05-threat-model.md) and [result schema](schema/lab05-result.schema.json).

## Security Console

The repository includes a local **Agentic AI Security Console** for orchestrating Labs 01-05 as hunts, preserving run history, generating findings from deterministic lab results, and presenting attack-path evidence.

**Objective:** determine whether an agentic application can cross a security boundary that should remain enforced—memory, tool approval, retrieval trust, delegated authority, or credential scope.

Install the repo in editable mode, then run:

    python -m pip install -e ".[dev]"
    agentic-ai-console

Open `http://127.0.0.1:8877`.

The website now has three distinct product areas:

- **Academy** — gamified learning paths, missions, XP/ranks, hands-on labs/hunts, and complete visibility across all 16 MITRE ATLAS tactics (current mission links vs roadmap gaps).
- **Career Lab** — interview preparation across SOC, detection engineering, AppSec, product security, red/purple team, threat hunting, threat intelligence, DFIR, SOAR, cloud, IAM, DevSecOps, GRC, leadership, AI security, research, cryptography, and more.
- **Target Lab** — register a local repository or GitHub URL, discover likely security surfaces, scaffold trusted adapters, and run compatible AASL security invariants against your own application.

The operations console still includes:

- Command Center with live posture and assessment coverage
- guided Hunts with objectives, steps, difficulty, controls, and points
- lab/scenario runner wired directly to the Python implementations
- explainable Control, Exposure, and Evidence scores
- Findings generated only when lab evidence supports them
- attack-path visualization
- run timeline and evidence drill-down
- local JSONL run/case persistence
- command palette (`Cmd/Ctrl + K`)
- no external frontend CDN or cloud dependency

Product documentation:

- [Platform / Console Architecture](docs/security-console.md)
- [Academy](docs/academy.md)
- [Career Lab](docs/career-lab.md)
- [Target Lab](docs/target-lab.md)
- [Scoring Model](docs/console-scoring.md)
- [Test Your Own Application](docs/test-your-app.md)
- [Target Adapter Manifest](docs/target-manifest.md)
- [Product Reference Models](docs/product-reference-models.md)

The console starts with a **Start Here** page that explains the workflow. The built-in console runs the deterministic reference harnesses; testing your own code requires connecting your application boundary through the documented adapter/wrapper pattern. Lab 01 is directly pluggable today.
## Repository principles

- **Reproducible over impressive** — tests should run without proprietary infrastructure where possible.
- **Behavioral evidence over prompt matching** — focus on security properties and observable boundaries.
- **Explicit controls** — distinguish a security failure from a broken test setup.
- **No fabricated telemetry** — sample artifacts are generated by the deterministic local harness.
- **Minimal sensitive data** — evidence should expose only what is required to support a finding.
- **Portable first** — the core lab uses the Python standard library; integrations can be added separately.

## Related open-source work

This lab is technically related to, but independent from, two public contribution threads:

- [NVIDIA garak #2453 — cross-actor isolation of persistent agent memory](https://github.com/NVIDIA/garak/issues/2453)
- [Elastic detection-rules #6722 — AWS Bedrock AgentCore cross-actor user-preference memory access](https://github.com/elastic/detection-rules/issues/6722)

Those projects have their own maintainer review processes. This repository does not imply that either proposal has been accepted.

## Scope

Lab 01 demonstrates the **security property and test methodology** with a deterministic local memory backend. It does not claim that any specific commercial service is vulnerable.

Provider-specific adapters should preserve the same controls and result semantics while replacing only the memory read/write transport.

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
```

CI runs the test suite on Python 3.11, 3.12, and 3.13.

## License

Apache-2.0.

## AI assistance

AI assistance was used during implementation and documentation. The repository owner is responsible for reviewing the code, tests, claims, and published results.
