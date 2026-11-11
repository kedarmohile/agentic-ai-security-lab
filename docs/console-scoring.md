# Security Console Scoring Model

The console uses three separate 0-100 scores. They summarize deterministic lab evidence; they are not CVSS, compliance attestations, or production claims.

## Control Score

Higher is better. Pass/controlled = 96, expected-authorized = 97, medium finding = 48, high finding = 22, inconclusive = 55.

## Exposure Score

Higher is worse. Pass/controlled = 14, expected-authorized = 8, medium finding = 66, high finding = 92, inconclusive = 35.

## Evidence Confidence

Completed deterministic runs normally score 96-98. A failed positive control caps confidence at 45 so a broken test setup cannot look authoritative.

## Posture Score

The Command Center posture is the mean Control Score of the latest run for each assessed lab. Unassessed labs are not silently treated as passing or failing. Assessment coverage is always shown beside posture.

## Hunt Points

Points are a research/learning mechanic, not a risk metric. Reproducing an evidence-supported finding earns full points. A conclusive controlled/pass result earns 35 percent of available points with a minimum of 150. Inconclusive runs earn zero.

## Academy mission completion

Academy progression is evidence-gated.

A mission linked to a lab is complete only when the user's stored run history contains both:

- the lab's secure scenario; and
- the lab's vulnerable scenario.

Reading content or opening a mission does not award completion.

## Academy XP and ranks

Current rank thresholds are:

| Rank | XP threshold |
| --- | ---: |
| Recruit | 0 |
| Analyst | 1,000 |
| Hunter | 2,500 |
| Operator | 4,500 |
| Specialist | 7,000 |
| Principal | 10,000 |

Mission XP is separate from Control / Exposure / Evidence scoring. It measures completed learning activity, not system security posture.

## Target Lab results

Target adapters must return at least:

- `finding`;
- `verdict`;
- `severity`.

Target Lab stores the returned result and target-run metadata. It does not silently manufacture Control / Exposure / Evidence scores for arbitrary third-party adapters. If a target adapter needs those scores, it should map its evidence to the same semantics explicitly rather than assuming built-in deterministic confidence.
