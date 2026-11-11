# Target Lab

Target Lab applies AASL security invariants to a repository or application that the user owns or is authorized to test.

## Objective

Move from:

```text
"Can the AASL reference harness reproduce this failure?"
```

to:

```text
"Can my application violate the same security boundary?"
```

## Supported target sources

### Local repository

Register an existing path, for example:

```text
/Users/Kedar/Documents/project/browser-agent
```

### GitHub repository

Register a GitHub clone URL or HTTPS repository URL.

Target Lab can perform an explicit shallow clone into the local AASL state directory before analysis.

Cloning does not execute target code.

## Target lifecycle

```text
Register
   ↓
Analyze
   ↓
Review detected capability signals
   ↓
Map compatible Labs 01-05
   ↓
Create Adapter Scaffold
   ↓
Add trusted target commands
   ↓
Run target security test
   ↓
Persist result
```

## Capability discovery

The current lightweight scanner looks for signals related to:

- memory / state;
- tools / browser / computer use;
- RAG / retrieval / vector stores;
- agents / handoffs / delegation;
- OAuth / tokens / credentials.

These matches are heuristic. They are suggestions, not proof that a target implements the corresponding security boundary.

## Compatible labs

The capability-to-lab mapping is currently:

| Capability signal | Lab |
| --- | --- |
| Memory | Lab 01 |
| Tools | Lab 02 |
| Retrieval | Lab 03 |
| Delegation / agent handoff | Lab 04 |
| Credentials / identity | Lab 05 |

## Adapter scaffold

**Create Adapter Scaffold** creates:

```text
target-repo/
├── .aasl/
│   └── target.json
└── security/
    └── aasl/
        └── README.md
```

The manifest starts with no commands.

AASL never adds an executable adapter command without the target owner explicitly configuring it.

## Active target execution

See [Target Adapter Manifest](target-manifest.md).

Target commands:

- are listed explicitly in `.aasl/target.json`;
- run without a shell;
- run from the target root;
- receive a minimal environment;
- have a 120-second timeout;
- must emit structured JSON;
- are persisted in `target_runs.jsonl`.

## Target result contract

At minimum:

```json
{
  "finding": false,
  "verdict": "pass",
  "severity": "none"
}
```

Adapters can add boundary-specific evidence.

## Security guidance

Only run Target Lab against repositories and systems you own or are authorized to test.

Prefer:

- test environments;
- synthetic identities;
- benign canaries;
- fake/test credentials;
- disposable resources;
- dry-run or simulated privileged actions.

## Relationship to Test Your Own Application

[Test Your Own Application](test-your-app.md) explains the security invariants and adapter patterns in detail.

Target Lab is the website workflow that registers, analyzes, scaffolds, and launches those explicitly configured adapters.
