# Academy

AASL Academy is the gamified learning and cyber-readiness surface of the platform.

## Objective

Learn an agentic-AI security boundary, reproduce a safe failure, prove the secure control, and preserve the evidence.

Mission completion is based on executed lab history, not passive reading.

## Learning model

AASL follows this loop:

```text
Learn the invariant
      ↓
Run the secure control
      ↓
Run the vulnerable condition
      ↓
Inspect evidence
      ↓
Complete the mission
      ↓
Advance to the next boundary
```

The product pattern is influenced by successful cyber-readiness platforms such as Hack The Box and Immersive, while using AASL's own content, code, scoring, and visual design. See [Product Reference Models](product-reference-models.md).

## Current learning paths

### Agentic Security Foundations

- M-001 — Contain the Memory Boundary
- M-002 — Guard the Tool Boundary
- M-003 — Break the Poison Chain
- M-004 — Stop the Confused Deputy
- M-005 — Contain Credential Bleed

### Identity, Privilege & Delegation

A focused path through Labs 02, 04, and 05.

### Memory, RAG & Persistent Influence

A focused path through Labs 01 and 03.

## Mission completion

A mission linked to a lab is complete when the run history contains:

- the lab's secure scenario; and
- the lab's vulnerable scenario.

This ensures learners see both the intended control and the failure condition.

## XP and ranks

| Rank | XP |
| --- | ---: |
| Recruit | 0 |
| Analyst | 1,000 |
| Hunter | 2,500 |
| Operator | 4,500 |
| Specialist | 7,000 |
| Principal | 10,000 |

XP is a learning-progression metric. It is not a risk score.

## Security framework stack

Academy uses four complementary framework lenses:

- OWASP Top 10:2025 for general web/application security;
- OWASP Top 10 for LLM Applications 2026 for GenAI application risks;
- OWASP Top 10 for Agentic Applications 2026 for autonomous-agent risks;
- MITRE ATLAS for AI adversary tactics and techniques.

See [Security Framework Stack](security-frameworks.md).

## MITRE ATLAS coverage

Academy displays all 16 MITRE ATLAS tactics:

1. Reconnaissance
2. Resource Development
3. AI Attack Adaptation
4. Initial Access
5. AI Model Access
6. Execution
7. Persistence
8. Privilege Escalation
9. Defense Evasion
10. Credential Access
11. Discovery
12. Lateral Movement
13. Collection
14. Command and Control
15. Exfiltration
16. Impact

Current AASL content is marked:

- **mission-linked** when a current lab exercises a relevant security property;
- **roadmap** when there is not yet an executable mission.

Showing every tactic does not mean every ATLAS technique is already covered.

## Relationship to Operations views

Academy uses the same underlying lab engine as:

- Hunts;
- Runs;
- Findings;
- Evidence;
- Cases;
- Command Center.

That means mission progress is grounded in the same evidence used for security investigation.
