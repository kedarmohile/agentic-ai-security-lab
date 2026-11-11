"""Product experiences for Academy, Career Lab, and Target Lab."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .orchestration import LABS, RunStore


@dataclass(frozen=True)
class Mission:
    mission_id: str
    lab_id: str
    title: str
    objective: str
    xp: int
    prerequisite: str | None = None


ACADEMY_PATHS: tuple[dict[str, Any], ...] = (
    {
        "path_id": "path-foundations",
        "title": "Agentic Security Foundations",
        "summary": "Learn the five core trust boundaries by running secure and vulnerable scenarios side by side.",
        "missions": (
            Mission("M-001", "lab01", "Contain the Memory Boundary", "Prove one actor cannot read another actor's persistent memory.", 1000),
            Mission("M-002", "lab02", "Guard the Tool Boundary", "Prove untrusted context cannot become privileged approval.", 1100, "M-001"),
            Mission("M-003", "lab03", "Break the Poison Chain", "Separate ingestion, retrieval, directive exposure, and downstream influence.", 1200, "M-002"),
            Mission("M-004", "lab04", "Stop the Confused Deputy", "Prove downstream privilege cannot exceed original delegated authority.", 1400, "M-003"),
            Mission("M-005", "lab05", "Contain Credential Bleed", "Prove credentials cannot cross subject, audience, resource, or request scope.", 1500, "M-004"),
        ),
    },
    {
        "path_id": "path-identity",
        "title": "Identity, Privilege & Delegation",
        "summary": "A focused path through privileged tools, delegated authority, and credential scope.",
        "missions": (
            Mission("M-I01", "lab02", "Exact Tool Approval", "Establish exact-action authorization for privileged tools.", 900),
            Mission("M-I02", "lab04", "Delegation Chain Integrity", "Bind authority to principal, delegate, deputy, request, action, and resource.", 1200, "M-I01"),
            Mission("M-I03", "lab05", "Credential Scope Integrity", "Separate credential exposure from successful unauthorized use.", 1300, "M-I02"),
        ),
    },
    {
        "path_id": "path-memory-rag",
        "title": "Memory, RAG & Persistent Influence",
        "summary": "Focus on state isolation, delayed retrieval, poisoning, and provenance.",
        "missions": (
            Mission("M-R01", "lab01", "Cross-Actor Isolation", "Validate actor-scoped persistence.", 900),
            Mission("M-R02", "lab03", "Delayed Poisoning", "Prove retrieved untrusted content does not gain instruction authority.", 1300, "M-R01"),
        ),
    },
)


ATLAS_TACTICS: tuple[dict[str, Any], ...] = (
    {"name": "Reconnaissance", "labs": (), "status": "roadmap"},
    {"name": "Resource Development", "labs": (), "status": "roadmap"},
    {"name": "AI Attack Adaptation", "labs": (), "status": "roadmap"},
    {"name": "Initial Access", "labs": (), "status": "roadmap"},
    {"name": "AI Model Access", "labs": (), "status": "roadmap"},
    {"name": "Execution", "labs": ("lab02",), "status": "mission-linked"},
    {"name": "Persistence", "labs": ("lab01", "lab03"), "status": "mission-linked"},
    {"name": "Privilege Escalation", "labs": ("lab04",), "status": "mission-linked"},
    {"name": "Defense Evasion", "labs": ("lab03",), "status": "mission-linked"},
    {"name": "Credential Access", "labs": ("lab05",), "status": "mission-linked"},
    {"name": "Discovery", "labs": (), "status": "roadmap"},
    {"name": "Lateral Movement", "labs": (), "status": "roadmap"},
    {"name": "Collection", "labs": ("lab01",), "status": "mission-linked"},
    {"name": "Command and Control", "labs": (), "status": "roadmap"},
    {"name": "Exfiltration", "labs": (), "status": "roadmap"},
    {"name": "Impact", "labs": ("lab02", "lab03"), "status": "mission-linked"},
)


COMMERCIAL_REFERENCES: tuple[dict[str, Any], ...] = (
    {
        "name": "Hack The Box Enterprise",
        "purpose": "Commercial learning / readiness pattern",
        "pattern": "Assess → Build → Drill → Measure → Repeat",
        "note": "Reference pattern only; AASL is not affiliated with Hack The Box.",
        "url": "https://www.hackthebox.com/business/enterprise-platform",
    },
    {
        "name": "Immersive",
        "purpose": "Framework coverage / evidence pattern",
        "pattern": "Hands-on exercises + resilience scoring + MITRE ATLAS readiness heatmap",
        "note": "Reference pattern only; AASL is not affiliated with Immersive.",
        "url": "https://www.immersivelabs.com/solutions/cyber-resilience-metrics",
    },
)


ROLE_TRACKS: tuple[dict[str, Any], ...] = (
    {
        "role_id": "soc-analyst", "name": "SOC Analyst", "group": "Protection & Defense",
        "summary": "Alert triage, investigation, escalation, telemetry reasoning, and incident handling.",
        "focus": ("SIEM", "EDR", "network telemetry", "triage", "incident severity", "MITRE ATT&CK"),
    },
    {
        "role_id": "detection-engineer", "name": "Detection Engineer", "group": "Protection & Defense",
        "summary": "Behavior-based detections, telemetry design, validation, tuning, and detection-as-code.",
        "focus": ("Sigma", "KQL/ES|QL", "ATT&CK", "data quality", "unit tests", "coverage"),
    },
    {
        "role_id": "threat-hunter", "name": "Threat Hunter", "group": "Protection & Defense",
        "summary": "Hypothesis-driven hunting across endpoint, identity, cloud, network, and application telemetry.",
        "focus": ("hypothesis", "ATT&CK", "querying", "baselining", "hunt-to-detection", "anomaly validation"),
    },
    {
        "role_id": "incident-response-dfir", "name": "Incident Response / DFIR", "group": "Protection & Defense",
        "summary": "Containment, forensic scoping, evidence preservation, eradication, and recovery.",
        "focus": ("forensics", "timeline analysis", "containment", "ransomware", "root cause", "recovery"),
    },
    {
        "role_id": "threat-intel", "name": "Threat Intelligence / SecIntel", "group": "Protection & Defense",
        "summary": "Threat actor, campaign, TTP, infrastructure, and intelligence-to-action analysis.",
        "focus": ("PIRs", "TTPs", "IOC lifecycle", "confidence", "attribution", "STIX/TAXII"),
    },
    {
        "role_id": "malware-analysis", "name": "Malware Analyst", "group": "Protection & Defense",
        "summary": "Static/dynamic analysis, behavioral clustering, sandboxing, and reverse-engineering reasoning.",
        "focus": ("sandboxing", "YARA", "behavior", "unpacking", "network indicators", "evasion"),
    },
    {
        "role_id": "red-team", "name": "Red Team / Adversary Simulation", "group": "Protection & Defense",
        "summary": "Goal-oriented adversary simulation, stealth, attack paths, operational safety, and reporting.",
        "focus": ("ATT&CK", "OPSEC", "identity", "lateral movement", "attack paths", "rules of engagement"),
    },
    {
        "role_id": "penetration-testing", "name": "Penetration Tester", "group": "Protection & Defense",
        "summary": "Scoped technical testing of web, API, network, cloud, and infrastructure attack surfaces.",
        "focus": ("web testing", "API testing", "network", "cloud", "reporting", "exploit validation"),
    },
    {
        "role_id": "purple-team", "name": "Purple Team", "group": "Protection & Defense",
        "summary": "Collaborative emulation-to-detection validation and control improvement.",
        "focus": ("ATT&CK", "emulation plans", "detection gaps", "control validation", "feedback loops"),
    },
    {
        "role_id": "vulnerability-management", "name": "Vulnerability Management", "group": "Protection & Defense",
        "summary": "Asset-aware vulnerability prioritization, remediation, exposure validation, and risk reduction.",
        "focus": ("CVSS", "EPSS", "KEV", "asset criticality", "exposure", "remediation SLAs"),
    },
    {
        "role_id": "appsec", "name": "Application Security", "group": "Design & Development",
        "summary": "Secure SDLC, threat modeling, code review, SAST/DAST, dependency risk, and developer enablement.",
        "focus": ("OWASP", "threat modeling", "SAST", "DAST", "SCA", "secure design"),
    },
    {
        "role_id": "product-security", "name": "Product Security", "group": "Design & Development",
        "summary": "Security architecture, abuse cases, secure defaults, product risk, and vulnerability response.",
        "focus": ("secure defaults", "abuse cases", "architecture", "PSIRT", "security reviews", "customer risk"),
    },
    {
        "role_id": "cloud-security", "name": "Cloud Security Engineer", "group": "Design & Development",
        "summary": "Cloud IAM, network, workload, data, KMS, logging, posture, and platform guardrails.",
        "focus": ("IAM", "KMS", "CSPM", "workload identity", "logging", "cloud-native controls"),
    },
    {
        "role_id": "devsecops", "name": "DevSecOps / Platform Security", "group": "Design & Development",
        "summary": "Secure pipelines, build integrity, policy-as-code, secrets, containers, and deployment controls.",
        "focus": ("CI/CD", "SBOM", "secrets", "containers", "IaC", "policy-as-code"),
    },
    {
        "role_id": "security-architecture", "name": "Security Architect", "group": "Design & Development",
        "summary": "Enterprise and solution security architecture, trust boundaries, patterns, and risk tradeoffs.",
        "focus": ("zero trust", "threat modeling", "identity", "data flows", "reference architectures", "risk"),
    },
    {
        "role_id": "soar-security-automation", "name": "SOAR / Security Automation Engineer", "group": "Implementation & Operation",
        "summary": "Automated enrichment, containment, orchestration, case workflows, and safe response engineering.",
        "focus": ("SOAR", "playbooks", "APIs", "idempotency", "human approval", "rollback"),
    },
    {
        "role_id": "iam", "name": "Identity & Access Management", "group": "Implementation & Operation",
        "summary": "Authentication, authorization, federation, lifecycle, privileged access, and workload identity.",
        "focus": ("OAuth/OIDC", "SAML", "RBAC/ABAC", "PAM", "JIT", "workload identity"),
    },
    {
        "role_id": "network-security", "name": "Network Security Engineer", "group": "Implementation & Operation",
        "summary": "Segmentation, firewalls, secure connectivity, IDS/IPS, DNS, proxy, and network telemetry.",
        "focus": ("segmentation", "firewalls", "IDS/IPS", "DNS", "TLS", "network detection"),
    },
    {
        "role_id": "endpoint-security", "name": "Endpoint Security Engineer", "group": "Implementation & Operation",
        "summary": "EDR, hardening, application control, host telemetry, attack surface reduction, and response.",
        "focus": ("EDR", "hardening", "ASR", "application control", "host telemetry", "response"),
    },
    {
        "role_id": "grc-risk", "name": "GRC / Cyber Risk", "group": "Oversight & Governance",
        "summary": "Risk management, controls, compliance, policy, audit, exceptions, and business alignment.",
        "focus": ("NIST CSF", "ISO 27001", "SOC 2", "risk quantification", "controls", "audit"),
    },
    {
        "role_id": "security-program", "name": "Security Program Manager", "group": "Oversight & Governance",
        "summary": "Roadmaps, dependencies, metrics, executive communication, and cross-functional security delivery.",
        "focus": ("roadmaps", "KPIs", "dependencies", "governance", "stakeholders", "delivery"),
    },
    {
        "role_id": "security-leadership", "name": "CISO / Security Leadership", "group": "Oversight & Governance",
        "summary": "Enterprise risk ownership, strategy, operating model, board communication, resilience, and investment.",
        "focus": ("strategy", "board", "risk appetite", "budget", "operating model", "resilience"),
    },
    {
        "role_id": "supply-chain-security", "name": "Cybersecurity Supply Chain Risk", "group": "Oversight & Governance",
        "summary": "Third-party, software supply chain, vendor, dependency, provenance, and concentration risk.",
        "focus": ("third-party risk", "SBOM", "provenance", "vendor assurance", "concentration", "dependencies"),
    },
    {
        "role_id": "ai-security", "name": "AI / GenAI / Agentic AI Security", "group": "Specialized / Emerging",
        "summary": "Model, agent, RAG, tool, identity, memory, data, and AI governance security.",
        "focus": ("prompt injection", "RAG", "agents", "memory", "tool authorization", "AI RMF"),
    },
    {
        "role_id": "security-research", "name": "Security Researcher", "group": "Specialized / Emerging",
        "summary": "Novel attack research, reproducibility, exploitability analysis, and responsible disclosure.",
        "focus": ("research method", "reproduction", "root cause", "PoC safety", "disclosure", "measurement"),
    },
    {
        "role_id": "cryptography", "name": "Cryptography / Key Management", "group": "Specialized / Emerging",
        "summary": "Cryptographic design, key lifecycle, protocol usage, migration, and implementation risk.",
        "focus": ("KMS/HSM", "TLS", "signatures", "key rotation", "PKI", "post-quantum migration"),
    },
)


def academy_catalog() -> dict[str, Any]:
    return {
        "paths": [
            {
                **{k: v for k, v in path.items() if k != "missions"},
                "missions": [asdict(m) for m in path["missions"]],
            }
            for path in ACADEMY_PATHS
        ],
        "atlas_tactics": list(ATLAS_TACTICS),
        "references": list(COMMERCIAL_REFERENCES),
    }


def academy_progress(store: RunStore) -> dict[str, Any]:
    runs = store.runs()
    by_lab: dict[str, set[str]] = {}
    for run in runs:
        by_lab.setdefault(run["lab_id"], set()).add(run["mode"])

    completed: set[str] = set()
    xp = 0
    mission_rows: list[dict[str, Any]] = []
    for path in ACADEMY_PATHS:
        for mission in path["missions"]:
            lab = LABS[mission.lab_id]
            secure_done = lab["secure_mode"] in by_lab.get(mission.lab_id, set())
            vulnerable_done = lab["vulnerable_mode"] in by_lab.get(mission.lab_id, set())
            is_complete = secure_done and vulnerable_done
            unlocked = mission.prerequisite is None or mission.prerequisite in completed
            if is_complete:
                completed.add(mission.mission_id)
                xp += mission.xp
            mission_rows.append({
                **asdict(mission),
                "secure_done": secure_done,
                "vulnerable_done": vulnerable_done,
                "complete": is_complete,
                "unlocked": unlocked,
            })

    rank = "Recruit"
    next_rank = None
    for threshold, name in ((0, "Recruit"), (1000, "Analyst"), (2500, "Hunter"), (4500, "Operator"), (7000, "Specialist"), (10000, "Principal")):
        if xp >= threshold:
            rank = name
        elif next_rank is None:
            next_rank = {"name": name, "xp": threshold}

    return {
        "xp": xp,
        "rank": rank,
        "next_rank": next_rank,
        "missions": mission_rows,
        "completed": len(completed),
        "total": len(mission_rows),
    }


def career_catalog() -> dict[str, Any]:
    return {
        "framework": {
            "name": "NIST NICE Framework Components",
            "version": "2.2.0",
            "work_roles": 42,
            "categories": 5,
            "competency_areas": 11,
            "note": "AASL uses NICE concepts for breadth and structure; the job-title tracks below are practical interview tracks, not claims of exact NICE Work Role equivalence.",
        },
        "roles": list(ROLE_TRACKS),
        "levels": ("entry", "mid", "senior", "principal", "manager", "executive"),
    }


def interview_session(role_id: str, level: str = "senior") -> dict[str, Any]:
    role = next((r for r in ROLE_TRACKS if r["role_id"] == role_id), None)
    if role is None:
        raise ValueError(f"unknown role: {role_id}")
    if level not in {"entry", "mid", "senior", "principal", "manager", "executive"}:
        raise ValueError(f"unsupported level: {level}")

    focus = role["focus"]
    questions = [
        {"dimension": "Technical depth", "question": f"Explain the core principles behind {focus[0]}, {focus[1]}, and {focus[2]}. Where do they commonly fail in production?"},
        {"dimension": "Architecture", "question": f"Design a secure operating model for {role['name']} in a large enterprise. Show trust boundaries, telemetry, control points, and failure handling."},
        {"dimension": "Adversarial scenario", "question": f"You discover a high-confidence security failure in the {role['name']} domain during a critical launch. Walk through triage, containment, evidence, and decision-making."},
        {"dimension": "Proactive security", "question": f"What would you do proactively in the first 90 days to reduce risk in {role['name']} before incidents occur?"},
        {"dimension": "Metrics", "question": f"Which 3-5 metrics prove a {role['name']} program is reducing risk rather than producing activity?"},
        {"dimension": "Hands-on", "question": f"Describe a hands-on example where you personally used or implemented {focus[0]} or {focus[1]}. What changed measurably?"},
        {"dimension": "Tradeoffs", "question": f"A business-critical launch conflicts with one of your {role['name']} controls. How do you decide whether to block, mitigate, redesign, or accept risk?"},
        {"dimension": "Behavioral / influence", "question": "Tell me about a time you disagreed with engineering, operations, or leadership on a security decision. How did you influence the outcome?"},
    ]
    if level in {"principal", "manager", "executive"}:
        questions.extend([
            {"dimension": "Scale", "question": f"How would you build a 12-month {role['name']} strategy across a global enterprise, including operating model, staffing, funding, and executive reporting?"},
            {"dimension": "Leadership", "question": f"How do you decide what your {role['name']} team should own directly versus federate to engineering or operations?"},
        ])

    return {
        "role": role,
        "level": level,
        "questions": questions,
        "scorecard": ("correctness", "depth", "structure", "risk judgment", "practicality", "metrics", "communication"),
    }


class TargetRegistry:
    """Local registry and lightweight capability scanner for user targets."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.path = state_dir / "targets.json"
        self.clone_root = state_dir / "target_repos"
        self.runs_path = state_dir / "target_runs.jsonl"

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")

    def targets(self) -> list[dict[str, Any]]:
        return self._read()

    def target_runs(self) -> list[dict[str, Any]]:
        if not self.runs_path.exists():
            return []
        rows = [json.loads(line) for line in self.runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return list(reversed(rows))

    def register(self, name: str, source_type: str, location: str) -> dict[str, Any]:
        name = name.strip()
        source_type = source_type.strip().lower()
        location = location.strip()
        if not name or not location:
            raise ValueError("target name and location are required")
        if source_type not in {"local", "github"}:
            raise ValueError("source_type must be local or github")

        target_id = "target-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        target = {
            "target_id": target_id,
            "name": name,
            "source_type": source_type,
            "location": location,
            "local_path": location if source_type == "local" else None,
            "analysis": None,
        }
        rows = [r for r in self._read() if r["target_id"] != target_id]
        rows.append(target)
        self._write(rows)
        return target

    def _find(self, target_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        rows = self._read()
        target = next((r for r in rows if r["target_id"] == target_id), None)
        if target is None:
            raise ValueError(f"unknown target: {target_id}")
        return rows, target

    def clone_github(self, target_id: str) -> dict[str, Any]:
        rows, target = self._find(target_id)
        if target["source_type"] != "github":
            raise ValueError("only GitHub targets can be cloned")
        if not shutil.which("git"):
            raise ValueError("git is not installed")

        self.clone_root.mkdir(parents=True, exist_ok=True)
        destination = self.clone_root / target_id
        if destination.exists():
            shutil.rmtree(destination)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", target["location"], str(destination)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("git clone failed: " + (result.stderr.strip() or "unknown error"))
        target["local_path"] = str(destination)
        self._write(rows)
        return self.analyze(target_id)

    def analyze(self, target_id: str) -> dict[str, Any]:
        rows, target = self._find(target_id)
        local_path = target.get("local_path")
        if not local_path:
            target["analysis"] = {
                "status": "registered",
                "message": "GitHub target registered. Use Clone & Analyze to create a local assessment copy.",
                "signals": [],
                "compatible_labs": [],
                "manifest": False,
            }
        else:
            root = Path(local_path).expanduser().resolve()
            if not root.is_dir():
                target["analysis"] = {
                    "status": "path-not-found",
                    "message": f"Local path does not exist: {root}",
                    "signals": [],
                    "compatible_labs": [],
                    "manifest": False,
                }
            else:
                target["analysis"] = self._scan_local(root)
        self._write(rows)
        return target

    @staticmethod
    def _scan_local(root: Path) -> dict[str, Any]:
        ignored = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".next"}
        extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rs", ".rb", ".cs", ".yaml", ".yml", ".json", ".toml"}
        keyword_groups = {
            "memory": ("memory", "checkpoint", "state_store", "state store", "redis"),
            "retrieval": ("rag", "retriev", "vector", "embedding", "faiss", "pinecone", "chroma"),
            "tools": ("tool", "function_call", "function call", "browser", "computer_use", "computer use"),
            "delegation": ("agent", "subagent", "handoff", "delegate", "supervisor", "orchestrator"),
            "credentials": ("oauth", "token", "credential", "bearer", "api key", "workload identity"),
        }

        signals: dict[str, int] = {k: 0 for k in keyword_groups}
        scanned = 0
        for path in root.rglob("*"):
            if scanned >= 700:
                break
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            if any(part in ignored for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:250_000].lower()
            except OSError:
                continue
            scanned += 1
            for group, words in keyword_groups.items():
                if any(word in text for word in words):
                    signals[group] += 1

        mapping = {
            "memory": "lab01",
            "tools": "lab02",
            "retrieval": "lab03",
            "delegation": "lab04",
            "credentials": "lab05",
        }
        compatible = [lab for group, lab in mapping.items() if signals[group] > 0]
        manifest_path = root / ".aasl" / "target.json"
        return {
            "status": "analyzed",
            "message": f"Scanned {scanned} source/config files. Capability matches are heuristic and must be confirmed before running target adapters.",
            "signals": [{"capability": k, "hits": v} for k, v in signals.items()],
            "compatible_labs": compatible,
            "manifest": manifest_path.is_file(),
            "manifest_path": str(manifest_path),
        }

    def scaffold(self, target_id: str) -> dict[str, Any]:
        _, target = self._find(target_id)
        local_path = target.get("local_path")
        if not local_path:
            raise ValueError("target must be local or cloned before scaffolding")
        root = Path(local_path).expanduser().resolve()
        aasldir = root / ".aasl"
        docsdir = root / "security" / "aasl"
        aasldir.mkdir(parents=True, exist_ok=True)
        docsdir.mkdir(parents=True, exist_ok=True)
        manifest = aasldir / "target.json"
        if not manifest.exists():
            manifest.write_text(json.dumps({"version": 1, "commands": {}}, indent=2) + "\n", encoding="utf-8")
        readme = docsdir / "README.md"
        if not readme.exists():
            readme.write_text(
                "# AASL target adapters\\n\\n"
                "Add one safe test command per supported lab to `.aasl/target.json`. "
                "Commands run without a shell from the repository root and must write one JSON object "
                "to stdout containing at least `finding`, `verdict`, and `severity`. "
                "Use `{mode}` in an argument to receive the selected scenario.\\n",
                encoding="utf-8",
            )
        return self.analyze(target_id)

    def run(self, target_id: str, lab_id: str, mode: str) -> dict[str, Any]:
        rows, target = self._find(target_id)
        del rows
        local_path = target.get("local_path")
        if not local_path:
            raise ValueError("target must be local or cloned before execution")
        root = Path(local_path).expanduser().resolve()
        manifest_path = root / ".aasl" / "target.json"
        if not manifest_path.is_file():
            raise ValueError("target adapter manifest not found: .aasl/target.json")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        commands = manifest.get("commands", {})
        raw = commands.get(lab_id)
        if raw is None:
            raise ValueError(f"target manifest has no command for {lab_id}")
        if not isinstance(raw, list) or not raw or not all(isinstance(v, str) for v in raw):
            raise ValueError("target command must be a JSON array of strings")
        command = [part.replace("{mode}", mode) for part in raw]

        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "AASL_TARGET_MODE": "1",
            "AASL_LAB_ID": lab_id,
            "AASL_SCENARIO": mode,
        }
        result = subprocess.run(
            command,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("target adapter failed: " + (result.stderr.strip() or f"exit {result.returncode}"))
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("target adapter must write one JSON result to stdout") from exc
        for required in ("finding", "verdict", "severity"):
            if required not in payload:
                raise ValueError(f"target adapter result missing: {required}")
        record = {
            "target_run_id": "TR-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_id": target_id,
            "target_name": target["name"],
            "lab_id": lab_id,
            "mode": mode,
            "result": payload,
            "command": command,
        }
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.runs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record
