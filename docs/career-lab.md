# Career Lab

Career Lab is AASL's role-based cybersecurity interview-preparation experience.

## Objective

Prepare for a security interview from multiple angles rather than memorizing isolated questions.

Each generated session covers some combination of:

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

## Seniority levels

Career Lab supports:

- Entry
- Mid
- Senior
- Principal
- Manager
- Executive

Principal, manager, and executive sessions include additional scale and leadership questions.

## Current role tracks

Career Lab currently includes practical tracks for:

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

The current framework context exposed in the product is:

- NICE Framework Components v2.2.0;
- 42 Work Roles;
- 5 Work Role Categories;
- 11 Competency Areas.

AASL's role tracks are practical job-title interview tracks. They are not presented as one-to-one NICE Work Roles.

## Session generation

The Career Lab API accepts:

```json
{
  "role_id": "ai-security",
  "level": "principal"
}
```

and returns:

- selected role metadata;
- selected seniority;
- multi-angle interview questions;
- a scorecard covering correctness, depth, structure, risk judgment, practicality, metrics, and communication.

## Relationship to Academy

Academy trains hands-on security reasoning.

Career Lab tests whether the user can explain, architect, prioritize, measure, and communicate the same kinds of security decisions in an interview setting.

The two experiences are intentionally separate but complementary.
