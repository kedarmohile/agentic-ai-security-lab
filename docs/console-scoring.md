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