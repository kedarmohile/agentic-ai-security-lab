# Feature Acceptance Audit

Audit date: **2026-11-11**

Statuses:

- **WORKS** — implementation and handler/API contract exist.
- **DEPENDENCY-GATED** — implemented, but requires a local/browser dependency.
- **ROADMAP** — visible by design but not yet implemented as a live service.
- **BACKEND-ONLY** — server capability exists but there is no current UI control.
- **FIXED-P0** — release-blocking defect found during this audit and corrected.

## P0 finding

### Console-wide interaction failure — FIXED-P0

Root cause:

- iterable selector calls were malformed as triple-dollar / quadruple-dollar helpers;
- those functions do not exist;
- browser startup failed before navigation and feature handlers were attached.

Impact:

- sidebar navigation could appear dead;
- product tabs could appear dead;
- Career Lab / Simulation controls could appear dead;
- pricing and dynamic feature actions could fail to initialize.

Fix:

- all iterable selectors now use exactly the double-dollar helper;
- CI rejects both 3+ dollar selector helpers and single-selector forEach patterns.

## Navigation and primary shell

| Feature | Status | Destination / behavior |
| --- | --- | --- |
| Start Here | WORKS | Academy |
| Pricing — sidebar | WORKS | Pricing page |
| Command Center | WORKS | Operations dashboard |
| Hunts | WORKS | Hunt inventory |
| Findings | WORKS | Evidence-supported findings |
| Runs | WORKS | Run history |
| Cases | WORKS | Investigation cases |
| Labs | WORKS | Labs 01-05 |
| Attack Graph | WORKS | Trust-boundary graph |
| Evidence | WORKS | Structured run evidence |
| Command palette | WORKS | Navigate views or execute lab modes |
| Pricing — top bar | WORKS | Pricing page |
| Run Hunt Pack | WORKS | Executes configured hunt pack |
| + Run Lab | WORKS | Opens lab runner drawer |
| Academy product tab | WORKS | Academy |
| Career Lab product tab | WORKS | Career Lab |
| Target Lab product tab | WORKS | Target Lab |
| Test Your Own App | WORKS | Routes directly to Target Lab |
| Open Target Lab | WORKS | Routes directly to Target Lab |

## Academy / lab operations

| Feature | Status | Notes |
| --- | --- | --- |
| Mission row | WORKS | Opens linked lab |
| Priority hunt row | WORKS | Opens hunt location |
| Run Hunt | WORKS | Executes recommended mode |
| Open Lab | WORKS | Opens lab runner |
| Run Lab | WORKS | Opens lab runner |
| Secure Control | WORKS | Executes secure mode |
| Quick Execute Scenario | WORKS | POST /api/run |
| Execute & Capture Evidence | WORKS | POST /api/run |
| Run details | WORKS | Timeline, scores, result |
| Open Evidence | WORKS | Opens run detail |
| Create Case | WORKS | Persists investigation case |
| Create Investigation Case | WORKS | Same action from detail drawer |
| Framework catalog | WORKS | Informational, not interactive |
| ATLAS tactic grid | WORKS | Informational coverage map |

## Career Lab — Interview Studio

| Feature | Status | Notes |
| --- | --- | --- |
| Role selection | WORKS | 26 role tracks |
| Entry / Mid / Senior / Principal / Manager / Executive | WORKS | Distinct level profiles |
| Interviewer persona selection | WORKS | Regenerates active session |
| Generate Session | WORKS | POST /api/interview |
| Evaluate Answer | WORKS | GenAI when enabled; deterministic fallback |
| Retry-to-mastery | WORKS | Attempts and best score persisted |
| Best sample answer | WORKS | Returned by evaluator |
| Improved learner answer | WORKS | Can be loaded back into editor |
| Ask aloud | DEPENDENCY-GATED | Browser speech synthesis |
| Answer by voice | DEPENDENCY-GATED | Browser speech recognition; typing fallback |

## Career Lab — Simulation Range

| Feature | Status | Notes |
| --- | --- | --- |
| Simulation Range tab | WORKS | Fixed by P0 selector correction |
| Role-specific scenario catalog | WORKS | POST /api/career/simulations |
| Scenario load | WORKS | Renders scenario artifacts/tasks |
| Artifact search workbench | WORKS | In-browser search |
| Show Hint | WORKS | Progressive hints; score penalty |
| Answer by voice | DEPENDENCY-GATED | Browser speech recognition |
| Validate Task | WORKS | POST /api/career/evaluate-simulation |
| Improved answer | WORKS | Can be loaded and retried |
| OWASP / ATLAS crosswalk | WORKS | Scenario-specific mappings |

## Local VM labs

| Feature | Status | Notes |
| --- | --- | --- |
| VM catalog | WORKS | Packaged Git blueprints |
| Start VM | DEPENDENCY-GATED | Requires Multipass |
| Reset VM | DEPENDENCY-GATED | Destroy/recreate selected AASL guest |
| Stop VM | DEPENDENCY-GATED | Requires Multipass |
| VM destroy API | BACKEND-ONLY | Endpoint exists; no current UI button |
| Hosted cloud VM | ROADMAP | Not deployed |
| Pro hosted lab entitlement | ROADMAP | Pricing defined; infrastructure not live |

## Target Lab

| Feature | Status | Notes |
| --- | --- | --- |
| Register local target | WORKS | Stores target locally |
| Register GitHub target | WORKS | Registration only |
| Analyze local target | WORKS | Heuristic capability scan |
| Clone & Analyze | DEPENDENCY-GATED | Requires local git + network access |
| Create Adapter Scaffold | WORKS | Creates .aasl/target.json scaffold |
| Run Target Test | DEPENDENCY-GATED | Requires explicit trusted adapter manifest |
| Target run history | WORKS | Stored in target_runs.jsonl |
| Automatic arbitrary-repo execution | NOT IMPLEMENTED BY DESIGN | Explicitly prohibited for safety |

## Pricing

| Feature | Status | Notes |
| --- | --- | --- |
| Pricing page | WORKS | /api/pricing |
| Monthly / Annual toggle | WORKS | Client-side price rendering |
| Free CTA | WORKS | Routes to Academy |
| Core CTA | WORKS | Routes to Career/Simulation preview |
| Pro CTA | ROADMAP PREVIEW | Hosted labs not live; routes to Simulation preview |
| Teams CTA | ROADMAP PREVIEW | Team product not live; routes to Target Lab foundation |
| Billing / checkout | ROADMAP | Explicitly not enabled |
| Subscription enforcement | ROADMAP | Explicitly not enabled |

## APIs

All JavaScript API routes used by the console have matching server routes.

Server-only capabilities include VM destroy. Target clone/scaffold and VM lifecycle actions are invoked indirectly through helper functions.

## Release gate

The test suite now checks:

- no malformed selector helpers;
- all static view/jump/scroll targets exist;
- UI API routes exist on the server;
- expected static control IDs have handlers;
- expected dynamic actions have generation + handler contracts;
- roadmap pricing is not presented as live;
- dependency-gated VM / voice / evaluator features preserve fallback messaging.

## Browser end-to-end release gate

A Playwright/Chromium acceptance workflow is now included under `.github/workflows/ui-acceptance.yml` and `tests_e2e/`.

It launches the real local console and exercises primary navigation, command palette, lab drawer, runs/evidence/findings/cases, pricing controls and CTAs, Career level/session evaluation, Simulation Range, dependency-gated VM feedback, and Target Lab local registration/scaffold behavior.

External-network-dependent actions such as cloning an arbitrary GitHub target are still treated as dependency-gated rather than being made a release-blocking third-party network test.