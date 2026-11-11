# Lab 03 Result Semantics

Lab 03 emits one JSON object per run.

## Fields

| Field | Meaning |
| --- | --- |
| `lab` | Stable Lab 03 identifier. |
| `run_id` | Per-run correlation identifier. |
| `lab_mode` | baseline, secure, vulnerable, or poison-not-retrieved. |
| `pipeline_mode` | secure provenance-aware handling or deliberately vulnerable directive-following behavior. |
| `baseline_control_correct` | Whether the clean corpus produced the expected answer before poison ingestion. |
| `poison_ingested` | Whether an untrusted document was persisted. |
| `poison_document_retrieved` | Whether any untrusted document entered the later retrieval set. |
| `trusted_fact_retrieved` | Whether the authoritative document remained in the retrieval set. |
| `untrusted_directive_detected` | Whether a retrieved untrusted directive was present. |
| `downstream_output_poisoned` | Whether the observed answer changed to the benign poison marker. |
| `retrieved_document_ids` | Ordered identifiers for the retrieval evidence. |
| `finding` | True only for confirmed downstream poisoning after a valid baseline. |
| `verdict` | pass, fail, or inconclusive. |
| `severity` | high for confirmed downstream influence; otherwise none. |
| `query_sha256` | Fingerprint of the benign query. |
| `expected_answer_sha256` | Fingerprint of the trusted answer. |
| `poison_marker_sha256` | Fingerprint of the benign poison marker. |
| `observed_answer_sha256` | Fingerprint of the observed answer, or null if no answer exists. |

## Interpretation

A retrieved poison with `downstream_output_poisoned=false` is **not** a finding in this lab.

The distinction is deliberate:

```text
persisted poison
      ↓
retrieved poison
      ↓
directive present
      ↓
downstream answer changed   ← confirmed finding
```

This keeps retrieval exposure, control failure, and demonstrated influence separate.
