# Security Console Architecture

The Agentic AI Security Console is a local operating surface for Labs 01-05.

## Design goals

- No fake telemetry. The dashboard is empty until a lab is executed.
- One evidence model. Every run becomes a structured record with scores, timeline, points, and optional finding.
- Local-first. No frontend CDN, hosted database, analytics service, or cloud runtime is required.
- Safe vulnerable scenarios. Vulnerable modes are deterministic simulations with no external side effects.
- Security-workflow feel. Hunts, findings, timelines, cases, evidence, and attack paths are first-class objects.

## Runtime

Browser -> local HTTP/JSON server -> orchestration layer -> Labs 01-05 -> append-only local run store.

The default state directory is .agentic-ai-security-lab/ and is git-ignored.

## API

| Endpoint | Method | Purpose |
| --- | --- | --- |
| /api/catalog | GET | Lab and hunt metadata |
| /api/status | GET | Current posture summary |
| /api/runs | GET | Local run history |
| /api/run | POST | Execute one lab scenario |
| /api/findings | GET | Findings derived from stored runs |
| /api/cases | GET/POST | Local investigation cases |

## Views

- Command Center: live posture, assessment coverage, priority hunts, recent runs.
- Hunts: hypothesis, objective, steps, controls, points, recommended scenario.
- Labs: all implemented scenarios and quick secure controls.
- Findings: only evidence-supported failures from executed runs.
- Runs: historical result comparison.
- Attack Graph: conceptual trust-boundary map.
- Evidence: raw structured lab output plus score context.
- Cases: local grouping of confirmed findings.

## Security boundary

The server binds to 127.0.0.1 by default and is intended for local research use. Authentication, TLS termination, multi-user isolation, and remote execution controls are not implemented and would be required before internet exposure.