"""Security-console orchestration for Labs 01-05.

Findings, scores, and timelines are derived from deterministic lab results.
The console does not seed or fabricate telemetry.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .credential_scope import LabMode as CredentialMode, run_credential_scope_lab
from .delegation_boundary import LabMode as DelegationMode, run_delegation_boundary_lab
from .memory_isolation import InMemoryPreferenceMemory, IsolationPolicy, NamespaceMode
from .memory_isolation import run_memory_isolation_lab
from .retrieval_poisoning import LabMode as RetrievalMode, run_retrieval_poisoning_lab
from .tool_authorization import LabMode as ToolMode, run_tool_authorization_lab


@dataclass(frozen=True)
class HuntDefinition:
    hunt_id: str
    lab_id: str
    title: str
    hypothesis: str
    objective: str
    difficulty: str
    points: int
    controls: int
    recommended_mode: str
    steps: tuple[str, ...]


LABS: dict[str, dict[str, Any]] = {
    "lab01": {
        "number": "01",
        "name": "Cross-Actor Persistent Memory Isolation",
        "domain": "Memory",
        "question": "Can Actor A memory cross into Actor B?",
        "modes": ("secure", "vulnerable", "shared-expected"),
        "secure_mode": "secure",
        "vulnerable_mode": "vulnerable",
        "threat_model": "docs/lab01-threat-model.md",
    },
    "lab02": {
        "number": "02",
        "name": "Tool Authorization Boundary",
        "domain": "Tools",
        "question": "Can untrusted context satisfy privileged tool approval?",
        "modes": ("secure", "vulnerable", "trusted-approved", "argument-substitution", "request-replay"),
        "secure_mode": "secure",
        "vulnerable_mode": "vulnerable",
        "threat_model": "docs/lab02-threat-model.md",
    },
    "lab03": {
        "number": "03",
        "name": "Retrieval / Persistent-Memory Poisoning",
        "domain": "Retrieval",
        "question": "Can persisted untrusted content change a later benign answer?",
        "modes": ("baseline", "secure", "vulnerable", "poison-not-retrieved"),
        "secure_mode": "secure",
        "vulnerable_mode": "vulnerable",
        "threat_model": "docs/lab03-threat-model.md",
    },
    "lab04": {
        "number": "04",
        "name": "Confused-Deputy Delegation",
        "domain": "Delegation",
        "question": "Can deputy privilege exceed the principal's delegated scope?",
        "modes": ("secure", "vulnerable", "exact-delegated", "resource-substitution", "delegate-substitution", "request-replay"),
        "secure_mode": "secure",
        "vulnerable_mode": "vulnerable",
        "threat_model": "docs/lab04-threat-model.md",
    },
    "lab05": {
        "number": "05",
        "name": "Agent Credential Scope Leakage",
        "domain": "Identity",
        "question": "Can credentials leak across agent identity or scope boundaries?",
        "modes": ("secure", "leaked-bound", "vulnerable", "derived-child", "audience-substitution", "resource-substitution", "request-replay"),
        "secure_mode": "secure",
        "vulnerable_mode": "vulnerable",
        "threat_model": "docs/lab05-threat-model.md",
    },
}


HUNTS: tuple[HuntDefinition, ...] = (
    HuntDefinition(
        "HUNT-001", "lab01", "Cross-Actor Memory Bleed",
        "A persistent memory namespace may be shared across principals that should be isolated.",
        "Determine whether memory written for Actor A can be retrieved by Actor B while persistence remains functional.",
        "Intermediate", 900, 5, "vulnerable",
        (
            "Establish Actor A persistence baseline",
            "Write a unique benign canary",
            "Start an independent Actor B session",
            "Attempt recall through the same memory key",
            "Correlate canary fingerprint and isolation verdict",
        ),
    ),
    HuntDefinition(
        "HUNT-002", "lab02", "Privileged Tool Approval Bypass",
        "Retrieved untrusted context may be mistaken for authorization to call a privileged tool.",
        "Prove whether an untrusted approval claim can cause a privileged action without a bound trusted approval.",
        "Advanced", 1250, 8, "vulnerable",
        (
            "Validate ordinary tool execution",
            "Inject the benign untrusted approval marker",
            "Attempt the privileged publish action",
            "Verify trusted approval binding",
            "Test argument substitution",
            "Test request replay",
            "Inspect decision source",
            "Generate finding only on unauthorized execution",
        ),
    ),
    HuntDefinition(
        "HUNT-003", "lab03", "Delayed Retrieval Poisoning",
        "Persisted untrusted content may be retrieved later and interpreted as instruction authority.",
        "Separate poison ingestion, retrieval, directive exposure, and demonstrated downstream influence.",
        "Advanced", 1400, 9, "vulnerable",
        (
            "Validate clean-corpus answer",
            "Persist benign poison document",
            "Run later benign query",
            "Confirm poison retrieval",
            "Confirm trusted fact remains reachable",
            "Detect untrusted directive",
            "Observe downstream answer",
            "Compare secure and vulnerable handling",
            "Preserve evidence fingerprints",
        ),
    ),
    HuntDefinition(
        "HUNT-004", "lab04", "Confused-Deputy Privilege Escalation",
        "A privileged deputy may confuse its own local capability with authority delegated by the original principal.",
        "Determine whether a narrow principal grant can be escalated through a more-privileged downstream agent.",
        "Expert", 1600, 10, "vulnerable",
        (
            "Prove exact delegation control works",
            "Confirm deputy local privilege exists",
            "Issue narrow principal delegation",
            "Request broader deputy action",
            "Verify principal binding",
            "Verify delegate binding",
            "Verify resource binding",
            "Verify request freshness",
            "Inspect authorization source",
            "Record execution outside valid delegation",
        ),
    ),
    HuntDefinition(
        "HUNT-005", "lab05", "Credential Bleed Between Agents",
        "A parent agent credential may be copied to a child agent and accepted outside its intended identity.",
        "Distinguish raw credential exposure from successful unauthorized use and validate safe child credential derivation.",
        "Expert", 1750, 10, "vulnerable",
        (
            "Validate parent credential for its owner",
            "Observe credential handoff boundary",
            "Compare parent and child credential fingerprints",
            "Verify subject binding",
            "Verify service audience binding",
            "Verify resource scope",
            "Verify request binding",
            "Attempt child action",
            "Test safe derived-child credential",
            "Classify exposure vs unauthorized-use severity",
        ),
    ),
)


def _run_lab01(mode: str) -> dict[str, Any]:
    if mode == "secure":
        backend = InMemoryPreferenceMemory(NamespaceMode.ACTOR_SCOPED)
        policy = IsolationPolicy(True)
    elif mode == "vulnerable":
        backend = InMemoryPreferenceMemory(NamespaceMode.SHARED)
        policy = IsolationPolicy(True)
    elif mode == "shared-expected":
        backend = InMemoryPreferenceMemory(NamespaceMode.SHARED)
        policy = IsolationPolicy(False)
    else:
        raise ValueError(f"unsupported Lab 01 mode: {mode}")
    return run_memory_isolation_lab(backend, policy=policy).to_dict()


RUNNERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "lab01": _run_lab01,
    "lab02": lambda mode: run_tool_authorization_lab(mode=ToolMode(mode)).to_dict(),
    "lab03": lambda mode: run_retrieval_poisoning_lab(mode=RetrievalMode(mode)).to_dict(),
    "lab04": lambda mode: run_delegation_boundary_lab(mode=DelegationMode(mode)).to_dict(),
    "lab05": lambda mode: run_credential_scope_lab(mode=CredentialMode(mode)).to_dict(),
}


FINDING_TITLES = {
    "lab01": "Cross-Actor Persistent Memory Isolation Failure",
    "lab02": "Privileged Tool Authorization Bypass",
    "lab03": "Delayed Retrieval Poisoning Changed Downstream Output",
    "lab04": "Confused-Deputy Delegation Escalation",
    "lab05": "Agent Credential Scope Boundary Failure",
}


def catalog() -> dict[str, Any]:
    return {
        "labs": [{"lab_id": lab_id, **metadata} for lab_id, metadata in LABS.items()],
        "hunts": [asdict(hunt) for hunt in HUNTS],
    }


def _score_result(result: dict[str, Any]) -> dict[str, int]:
    verdict = str(result.get("verdict", "inconclusive"))
    severity = str(result.get("severity", "none"))
    finding = bool(result.get("finding", False))

    if verdict == "inconclusive":
        control, exposure, evidence = 55, 35, 48
    elif finding and severity == "high":
        control, exposure, evidence = 22, 92, 98
    elif finding and severity == "medium":
        control, exposure, evidence = 48, 66, 96
    elif verdict == "expected-authorized":
        control, exposure, evidence = 97, 8, 97
    else:
        control, exposure, evidence = 96, 14, 97

    for control_name in (
        "baseline_control_correct",
        "actor_a_control_recall",
        "control_delegation_succeeded",
        "owner_control_succeeded",
    ):
        if result.get(control_name) is False:
            evidence = min(evidence, 45)

    return {"control": control, "exposure": exposure, "evidence": evidence}


def _timeline(lab_id: str, result: dict[str, Any]) -> list[dict[str, str]]:
    events = [{"phase": "prepare", "status": "complete", "message": "Scenario initialized with deterministic synthetic inputs."}]

    if lab_id == "lab01":
        events += [
            {"phase": "control", "status": "complete" if result.get("actor_a_control_recall") else "failed", "message": "Actor A persistence control evaluated."},
            {"phase": "boundary", "status": "alert" if result.get("actor_b_observed_canary") else "complete", "message": "Actor B recall checked against Actor A canary."},
        ]
    elif lab_id == "lab02":
        events += [
            {"phase": "control", "status": "complete" if result.get("ordinary_tool_control_executed") else "failed", "message": "Ordinary tool control evaluated."},
            {"phase": "approval", "status": "complete" if result.get("trusted_approval_valid_for_request") else "observed", "message": "Trusted approval binding evaluated."},
            {"phase": "execute", "status": "alert" if result.get("finding") else "complete", "message": "Privileged simulated tool decision recorded."},
        ]
    elif lab_id == "lab03":
        events += [
            {"phase": "baseline", "status": "complete" if result.get("baseline_control_correct") else "failed", "message": "Clean corpus baseline evaluated."},
            {"phase": "ingest", "status": "observed" if result.get("poison_ingested") else "complete", "message": "Untrusted persistence stage evaluated."},
            {"phase": "retrieve", "status": "observed" if result.get("poison_document_retrieved") else "complete", "message": "Later retrieval set evaluated."},
            {"phase": "influence", "status": "alert" if result.get("downstream_output_poisoned") else "complete", "message": "Downstream answer integrity evaluated."},
        ]
    elif lab_id == "lab04":
        events += [
            {"phase": "control", "status": "complete" if result.get("control_delegation_succeeded") else "failed", "message": "Exact delegation positive control evaluated."},
            {"phase": "capability", "status": "observed" if result.get("deputy_has_local_capability") else "failed", "message": "Deputy local privilege checked."},
            {"phase": "delegation", "status": "complete" if result.get("delegation_valid_for_request") else "observed", "message": "Original principal delegation scope evaluated."},
            {"phase": "execute", "status": "alert" if result.get("finding") else "complete", "message": "Deputy simulated action decision recorded."},
        ]
    else:
        events += [
            {"phase": "control", "status": "complete" if result.get("owner_control_succeeded") else "failed", "message": "Owner credential positive control evaluated."},
            {"phase": "handoff", "status": "alert" if result.get("parent_credential_exposed_to_child") else "complete", "message": "Cross-agent credential exposure evaluated."},
            {"phase": "scope", "status": "complete" if result.get("credential_exactly_valid_for_child_request") else "observed", "message": "Child credential exact scope evaluated."},
            {"phase": "execute", "status": "alert" if result.get("unauthorized_use_finding") else "complete", "message": "Synthetic child service decision recorded."},
        ]

    events.append({
        "phase": "verdict",
        "status": "alert" if result.get("finding") else "complete",
        "message": f"Run completed with verdict: {result.get('verdict', 'inconclusive')}.",
    })
    return events


def _finding(lab_id: str, result: dict[str, Any], run_id: str) -> dict[str, Any] | None:
    if not result.get("finding"):
        return None
    return {
        "finding_id": f"AASL-{LABS[lab_id]['number']}-{run_id[-6:].upper()}",
        "run_id": run_id,
        "lab_id": lab_id,
        "title": FINDING_TITLES[lab_id],
        "severity": str(result.get("severity", "high")),
        "status": "confirmed",
        "summary": LABS[lab_id]["question"],
        "evidence_keys": sorted(
            key for key, value in result.items()
            if isinstance(value, bool) and value
        ),
    }


def _hunt_points(lab_id: str, result: dict[str, Any]) -> dict[str, int]:
    hunt = next(h for h in HUNTS if h.lab_id == lab_id)
    if result.get("finding"):
        earned = hunt.points
    elif result.get("verdict") == "inconclusive":
        earned = 0
    else:
        earned = max(150, round(hunt.points * 0.35))
    return {"earned": earned, "possible": hunt.points}


def execute_lab(lab_id: str, mode: str) -> dict[str, Any]:
    if lab_id not in LABS:
        raise ValueError(f"unknown lab: {lab_id}")
    if mode not in LABS[lab_id]["modes"]:
        raise ValueError(f"unsupported mode for {lab_id}: {mode}")

    result = RUNNERS[lab_id](mode)
    run_id = str(result.get("run_id"))
    record = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "lab_id": lab_id,
        "lab_number": LABS[lab_id]["number"],
        "lab_name": LABS[lab_id]["name"],
        "domain": LABS[lab_id]["domain"],
        "mode": mode,
        "result": result,
        "scores": _score_result(result),
        "points": _hunt_points(lab_id, result),
        "timeline": _timeline(lab_id, result),
    }
    record["finding"] = _finding(lab_id, result, run_id)
    return record


class RunStore:
    """Append-only local JSONL store for console runs and cases."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.runs_path = state_dir / "runs.jsonl"
        self.cases_path = state_dir / "cases.jsonl"

    def _ensure(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def append_run(self, record: dict[str, Any]) -> None:
        self._ensure()
        with self.runs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def runs(self) -> list[dict[str, Any]]:
        return list(reversed(self._read(self.runs_path)))

    def findings(self) -> list[dict[str, Any]]:
        return [run["finding"] for run in self.runs() if run.get("finding") is not None]

    def cases(self) -> list[dict[str, Any]]:
        return list(reversed(self._read(self.cases_path)))

    def create_case(self, title: str, finding_id: str | None = None) -> dict[str, Any]:
        self._ensure()
        case = {
            "case_id": f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "finding_id": finding_id,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.cases_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(case, sort_keys=True) + "\n")
        return case


def status(store: RunStore) -> dict[str, Any]:
    runs = store.runs()
    findings = store.findings()
    latest_by_lab: dict[str, dict[str, Any]] = {}
    for run in runs:
        latest_by_lab.setdefault(run["lab_id"], run)

    assessed = len(latest_by_lab)
    posture = None
    evidence = None
    if assessed:
        posture = round(sum(run["scores"]["control"] for run in latest_by_lab.values()) / assessed)
        evidence = round(sum(run["scores"]["evidence"] for run in latest_by_lab.values()) / assessed)

    return {
        "posture_score": posture,
        "evidence_confidence": evidence,
        "assessed_labs": assessed,
        "total_labs": len(LABS),
        "total_runs": len(runs),
        "findings": len(findings),
        "high_findings": sum(1 for f in findings if f["severity"] == "high"),
        "medium_findings": sum(1 for f in findings if f["severity"] == "medium"),
        "cases": len(store.cases()),
    }
