# AASL Platform Architecture

AASL v0.7 is an open-source agentic AI security platform with three distinct product experiences that share one evidence engine.

## Product surfaces

### Academy

Gamified, evidence-gated learning:

- learning paths and missions;
- secure + vulnerable scenario completion;
- XP and operator ranks;
- guided hunts;
- all 16 MITRE ATLAS tactics visible as either mission-linked or roadmap;
- commercial product-pattern references shown as unaffiliated examples.

### Career Lab

Role-based interview preparation:

- 26 practical cybersecurity role tracks;
- entry, mid, senior, principal, manager, and executive levels;
- technical depth, architecture, proactive security, adversarial scenarios, metrics, hands-on execution, tradeoffs, behavioral influence, scale, and leadership;
- NIST NICE concepts used for breadth and structure without claiming one-to-one job-title equivalence.

### Target Lab

Assessment of user-owned or authorized repositories:

- local path registration;
- GitHub URL registration and explicit shallow clone;
- heuristic capability discovery;
- mapping to compatible Labs 01-05;
- explicit adapter scaffolding;
- trusted `.aasl/target.json` execution manifest;
- persisted target-run history.

Target Lab does not silently execute arbitrary repository code.

## Shared security engine

The five current labs remain the core security invariants:

1. cross-actor persistent memory isolation;
2. privileged tool authorization;
3. delayed retrieval / memory poisoning;
4. confused-deputy delegation;
5. agent credential scope leakage.

Built-in lab runs are deterministic and side-effect-free.

## Runtime

```text
Browser
  |
  | HTTP / JSON
  v
console_server.py
  |
  +-- orchestration.py
  |     +-- Labs 01-05
  |     +-- hunts
  |     +-- scores / findings / timelines
  |
  +-- product_experiences.py
  |     +-- Academy paths / missions / ATLAS map
  |     +-- Career role catalog / interview sessions
  |     +-- Target registry / analysis / adapters
  |
  +-- local state
        +-- runs.jsonl
        +-- cases.jsonl
        +-- targets.json
        +-- target_runs.jsonl
        +-- target_repos/
```

The default state directory is `.agentic-ai-security-lab/`. The recommended explicit local state directory is `local-data/console/`.

## HTTP API

### Core lab / operations APIs

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/catalog` | GET | Lab and hunt metadata |
| `/api/status` | GET | Current lab posture summary |
| `/api/runs` | GET | Built-in run history |
| `/api/run` | POST | Execute one built-in lab scenario |
| `/api/findings` | GET | Evidence-supported findings |
| `/api/cases` | GET/POST | Local investigation cases |

### Academy APIs

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/academy` | GET | Learning paths, missions, ATLAS tactics, reference patterns |
| `/api/academy/progress` | GET | XP, rank, and mission completion from actual lab runs |

### Career Lab APIs

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/career` | GET | Role catalog, levels, NICE framework context |
| `/api/interview` | POST | Generate a multi-angle interview session |

### Target Lab APIs

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/api/targets` | GET/POST | List or register targets |
| `/api/targets/analyze` | POST | Analyze a local target |
| `/api/targets/clone` | POST | Shallow-clone and analyze a GitHub target |
| `/api/targets/scaffold` | POST | Create adapter scaffold and empty manifest |
| `/api/targets/run` | POST | Run an explicitly configured trusted adapter |

## Website navigation

The three top-level product tabs are:

1. **Academy**
2. **Career Lab**
3. **Target Lab**

The security-operations views remain available underneath the platform:

- Command Center;
- Hunts;
- Findings;
- Runs;
- Cases;
- Labs;
- Attack Graph;
- Evidence.

## Security boundary

The local console binds to `127.0.0.1:8877` by default.

It is intended for local research and development. Authentication, TLS termination, multi-user isolation, and remote-execution controls are not implemented. Do not expose the server directly to the internet.

Target Lab execution has an additional trust boundary:

- analysis does not execute repository code;
- active target execution requires `.aasl/target.json`;
- commands run without a shell;
- commands run from the target repository root;
- the execution environment is intentionally minimal;
- execution has a 120-second timeout.

See [Target Adapter Manifest](target-manifest.md) for the target execution contract.
