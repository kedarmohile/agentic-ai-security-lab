# Career Lab

Career Lab combines two distinct preparation modes:

1. **Interview Studio** — answer role-specific interview questions and receive a score, strengths, missing concepts, an exemplar answer, and constructive improvement guidance.
2. **Simulation Range** — practice the work itself through synthetic logs, code, configurations, policies, incident timelines, sensitive-data artifacts, search tooling, hints, and task validation.

The goal is not Q&A memorization. It is to prepare for both the interview **and** the hands-on reasoning expected in the role.

## Security specialization

AASL keeps broad cybersecurity coverage, but specializes deeply in **GenAI and Agentic AI security**.

Career scenarios can be mapped through four complementary lenses:

- **OWASP Top 10:2025** — conventional web/application security risks;
- **OWASP Top 10 for LLM Applications 2026** — LLM / GenAI application risks;
- **OWASP Top 10 for Agentic Applications 2026** — autonomous-agent risk classes;
- **MITRE ATLAS** — AI adversary behaviors, tactics, and techniques.

A scenario only displays mappings that are genuinely relevant. Traditional AppSec scenarios are not forced into AI-specific categories.

See [Security Framework Stack](security-frameworks.md).

## Interview Studio

Choose a role and seniority:

- Entry
- Mid
- Senior
- Principal
- Manager
- Executive

Generated questions span:

- technical depth;
- architecture;
- adversarial scenarios;
- proactive security;
- metrics;
- hands-on implementation;
- risk tradeoffs;
- behavioral / influence;
- scale;
- leadership.

Each question includes an answer editor and **Evaluate Answer** action.

Career Lab uses a two-layer evaluator:

1. a deterministic local rubric that always works offline;
2. an optional GenAI evaluator using the OpenAI Responses API when `OPENAI_API_KEY` is configured.

The evaluation returns:

- weighted score;
- qualitative rating;
- strengths;
- specific missing concepts;
- critical but constructive improvement points;
- a best sample answer;
- an improved rewrite of the learner's own answer;
- attempt number, previous best, score delta, and best score;
- a mastery decision and next-attempt instruction.

The default mastery threshold is **95/100**. Learners can revise and resubmit the same answer until they reach mastery.

### Enable GenAI evaluation

The default model is `gpt-6-luna`. Override it with `AASL_EVAL_MODEL`.

```bash
export OPENAI_API_KEY="your-api-key"
export AASL_EVAL_PROVIDER="auto"
export AASL_EVAL_MODEL="gpt-6-luna"
export AASL_MASTERY_SCORE="95"

agentic-ai-console --port 8877 --state-dir local-data/console
```

If the API key is absent or the model call fails, AASL falls back to the deterministic local evaluator.

The API key is read from the process environment and is not stored by AASL.

### Weighted rubrics

The evaluator weights change by context.

For a normal interview answer, the rubric emphasizes:

- technical correctness;
- role depth;
- risk judgment;
- structure/communication;
- evidence/metrics;
- practicality.

Principal/manager sessions increase architecture, operating-model, scale, and influence weight.

Executive sessions emphasize:

- risk judgment and tradeoffs;
- enterprise scale and operating model;
- executive communication;
- technical correctness;
- metrics/accountability;
- practicality.

Simulation tasks emphasize technical correctness, evidence/reasoning, remediation/decision quality, completeness, and communication.

The evaluator is guidance, not a hiring decision.

## Interviewer personas and voice

Interview Studio includes interviewer personas with different styles, such as architecture-first, SOC/detection, red-team, and AppSec/product-security interviewers.

In supported browsers:

- **Ask aloud** uses browser speech synthesis to speak the question;
- **Answer by voice** uses browser speech recognition to transcribe the learner's response into the answer editor.

Voice is optional. Typed answers remain the universal fallback.

Browser speech recognition support varies by browser/platform; AASL does not require a voice API key for the browser-native mode.

## Simulation Range

Simulation Range is role-specific.

Examples include:

- SOC / threat hunting — correlate suspicious authentication and privilege events;
- detection engineering — design a behavior-based correlation from synthetic telemetry;
- DFIR — scope endpoint execution, persistence, network, and lateral-access evidence;
- threat intelligence — distinguish evidence, confidence, and unsupported attribution;
- malware analysis — interpret a synthetic sandbox trace;
- AppSec — identify BOLA/IDOR and design a regression test;
- red team / pentest — reason through a deliberately synthetic authorization bypass;
- cloud / IAM — reduce an over-broad policy to least privilege;
- SOAR — design a safe containment playbook with approval, idempotency, and rollback;
- sensitive-data discovery — build a basic search strategy and classify secrets/PII-like test data;
- vulnerability management — prioritize using exploitability, exposure, and asset criticality;
- security architecture — redesign agent/tool/credential trust boundaries;
- GRC / leadership — make a time-bound security exception decision;
- cryptography — review weak protocol/key lifecycle configuration;
- AI security — investigate prompt-injection-to-tool-execution and authorization-boundary failures.

## Search workbench and hints

Each simulation can expose synthetic artifacts directly in the website.

The built-in search workbench lets learners search those artifacts without leaving Career Lab.

Hints are progressive. Using a hint reduces the final task score so the learner can distinguish assisted completion from independent recall.

## Portable VM labs

Some exercises benefit from a real guest OS.

AASL uses **Git-stored VM blueprints**, not VM disk images.

The repository contains:

```text
src/agentic_ai_security_lab/vm_blueprints/
├── linux-soc-dfir/
├── linux-appsec/
└── linux-cloud-iam/
```

Each blueprint contains small text files:

- `lab.json`;
- `cloud-init.yaml`;
- synthetic lab artifacts.

The local console uses Multipass to materialize an Ubuntu guest appropriate for the host platform.

Supported host families:

- macOS;
- Windows;
- Linux.

The portable reset mechanism is **destroy and recreate from the Git blueprint**. Snapshot support is optional and never required for correctness.

See [Portable VM Labs](vm-labs.md).

## Current role tracks

Career Lab currently includes:

- SOC Analyst
- Detection Engineer
- Threat Hunter
- Incident Response / DFIR
- Threat Intelligence / SecIntel
- Malware Analyst
- Red Team / Adversary Simulation
- Penetration Tester
- Purple Team
- Vulnerability Management
- Application Security
- Product Security
- Cloud Security Engineer
- DevSecOps / Platform Security
- Security Architect
- SOAR / Security Automation Engineer
- Identity & Access Management
- Network Security Engineer
- Endpoint Security Engineer
- GRC / Cyber Risk
- Security Program Manager
- CISO / Security Leadership
- Cybersecurity Supply Chain Risk
- AI / GenAI / Agentic AI Security
- Security Researcher
- Cryptography / Key Management

## NIST NICE reference

Career Lab uses NIST NICE concepts for breadth and structure.

The product currently exposes:

- NICE Framework Components v2.2.0;
- 42 Work Roles;
- 5 Work Role Categories;
- 11 Competency Areas.

AASL's practical job-title tracks are not claimed as one-to-one NICE Work Roles.

## Local attempt history

Interview evaluations and simulation evaluations are stored locally in:

```text
career_attempts.jsonl
```

under the configured AASL state directory.

No external assessment service is required.

## Relationship to Academy

Academy provides structured learning paths and evidence-gated missions.

Career Lab tests two additional dimensions:

- can the learner **explain** the security decision in an interview?
- can the learner **perform the underlying security reasoning** in a realistic synthetic exercise?

The same framework language and security invariants connect both experiences.
