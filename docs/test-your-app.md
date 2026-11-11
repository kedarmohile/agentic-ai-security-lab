# Test Your Own Application

The built-in labs are **reference security harnesses**. They prove the test methodology, controls, evidence model, scoring, and investigation workflow.

They do **not** automatically scan an arbitrary repository.

To test your own agentic application, connect the relevant application boundary to the corresponding lab invariant.

## Objective

The platform is designed to answer:

> Can this agentic system cross a security boundary that should remain enforced?

The current five boundaries are:

| Lab | Boundary | Question |
| --- | --- | --- |
| 01 | Persistent memory | Can one actor retrieve another actor's memory? |
| 02 | Privileged tools | Can untrusted context satisfy or bypass tool approval? |
| 03 | Retrieval / RAG | Can persisted untrusted content alter a later benign result? |
| 04 | Delegation | Can a downstream deputy exceed the original principal's delegated authority? |
| 05 | Credentials / identity | Can credentials cross agent, audience, resource, or request boundaries? |

## Two ways to use the project

### 1. Reference mode

Use the Security Console or the built-in CLI scenarios.

This is useful for:

- understanding the security property;
- seeing a secure and vulnerable implementation side by side;
- validating the evidence model;
- training / tabletop exercises;
- building detection or regression logic;
- demonstrating the attack path safely.

### 2. Target mode

Replace the deterministic reference boundary with your own application boundary.

The test should preserve the same:

- positive control;
- negative control;
- expected policy;
- evidence fields;
- verdict logic.

## Support matrix today

| Lab | Direct target adapter today | What to connect |
| --- | --- | --- |
| Lab 01 | **Yes** | Any object implementing `remember()` and `recall()` |
| Lab 02 | Wrapper required | Your approval check + privileged tool invocation |
| Lab 03 | Wrapper required | Your ingestion + retrieval + downstream response path |
| Lab 04 | Wrapper required | Your delegation / principal-to-agent authorization path |
| Lab 05 | Wrapper required | Your identity/token issue + service authorization path |

The console currently executes the built-in deterministic scenarios. External-target registration in the UI is a future extension. You can already run target-mode tests from Python and then use the same result/evidence conventions.

## Lab 01 — working target adapter pattern

Lab 01 is directly pluggable because the runner accepts a memory backend implementing:

```python
remember(context, key, value) -> None
recall(context, key) -> str | None
```

Example:

```python
from agentic_ai_security_lab.memory_isolation import (
    MemoryContext,
    run_memory_isolation_lab,
)


class MyProductMemoryAdapter:
    def __init__(self, client):
        self.client = client

    def remember(self, context: MemoryContext, key: str, value: str) -> None:
        self.client.put_memory(
            actor_id=context.actor_id,
            session_id=context.session_id,
            key=key,
            value=value,
        )

    def recall(self, context: MemoryContext, key: str) -> str | None:
        return self.client.get_memory(
            actor_id=context.actor_id,
            session_id=context.session_id,
            key=key,
        )


client = build_your_real_client()
adapter = MyProductMemoryAdapter(client)

result = run_memory_isolation_lab(adapter)

print(result.to_dict())
```

The important point is that the test logic still owns the security assertion. Your adapter only translates the lab's actor/session/key operations into your product API.

## What a real Lab 01 integration tests

The harness will:

1. write a unique benign canary as Actor A;
2. start a new Actor A session;
3. prove persistence works;
4. start Actor B;
5. attempt to retrieve the same memory key;
6. fail if Actor B sees Actor A's canary while isolation is expected.

If Actor A cannot retrieve its own memory, the test becomes **inconclusive**, not pass.

## Lab 02 — map your privileged tool boundary

Your wrapper should expose these stages:

```text
untrusted context
      ↓
agent proposes privileged action
      ↓
your approval / authorization check
      ↓
your tool invocation boundary
      ↓
observed allowed / denied result
```

Preserve these controls:

- an ordinary non-privileged action works;
- untrusted text does not become approval;
- approval is bound to the exact action and arguments;
- approval cannot be replayed for another request.

Do not test by executing a destructive real action. Use a safe test resource, dry-run path, mock service, or disposable environment.

## Lab 03 — map your RAG / retrieval path

Your target test should measure these stages separately:

```text
untrusted content accepted
      ↓
persisted / indexed
      ↓
retrieved by later benign query
      ↓
untrusted directive reaches downstream context
      ↓
final answer or behavior changes
```

A poison document being retrieved is **not** by itself a confirmed finding.

The finding requires downstream influence after a valid clean baseline.

## Lab 04 — map your delegation chain

Model:

```text
original principal
      ↓
Agent A
      ↓
more-privileged Agent B / deputy
      ↓
protected action
```

Record:

- original principal;
- delegate;
- deputy;
- request;
- action;
- resource;
- exact authority delegated;
- final allow / deny decision.

The key assertion is that the deputy's own privilege must not substitute for the principal's delegated authority.

## Lab 05 — map your identity / credential path

Record:

- credential owner / subject;
- receiving agent;
- audience / service;
- action;
- resource;
- request identifier;
- whether the same raw token crossed the agent boundary;
- whether the receiving agent could actually use it.

Keep **credential exposure** separate from **successful unauthorized use**.

## Recommended target workflow

For each real application:

1. Pick one boundary.
2. Run the built-in secure and vulnerable reference scenarios.
3. Implement the thin adapter/wrapper for your application.
4. Run in a test or disposable environment.
5. Preserve the positive control.
6. Capture only the evidence required to prove the result.
7. Map the result into the same verdict and severity semantics.
8. Add a regression test to your CI.

## Example target directory

A clean project layout could be:

```text
your-agent-project/
├── src/
├── tests/
└── security/
    └── aasl/
        ├── memory_adapter.py
        ├── tool_authorization_test.py
        ├── retrieval_poisoning_test.py
        ├── delegation_test.py
        └── credential_scope_test.py
```

This keeps security tests close to the application without copying the entire lab implementation.

## Safety

Only run target-mode tests against systems you own or are authorized to test.

Prefer:

- synthetic test identities;
- benign canaries;
- disposable resources;
- dry-run tool calls;
- non-production memory namespaces;
- fake or test credentials;
- reversible actions.

The reference labs intentionally use synthetic data and in-memory side effects for this reason.
