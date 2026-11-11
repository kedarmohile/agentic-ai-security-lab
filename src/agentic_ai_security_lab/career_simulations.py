"""Interactive Career Lab interview evaluation and role-specific simulations.

All scenarios are synthetic and designed for local learning. They do not target
real systems, credentials, or organizations.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .security_frameworks import framework_catalog


@dataclass(frozen=True)
class SimulationTask:
    task_id: str
    title: str
    prompt: str
    answer_type: str
    required_concepts: tuple[tuple[str, ...], ...]
    bonus_concepts: tuple[tuple[str, ...], ...]
    model_answer: str
    hints: tuple[str, ...]


@dataclass(frozen=True)
class CareerScenario:
    scenario_id: str
    title: str
    category: str
    difficulty: str
    briefing: str
    objectives: tuple[str, ...]
    artifacts: tuple[dict[str, str], ...]
    tasks: tuple[SimulationTask, ...]
    skills: tuple[str, ...]


def _concept(*aliases: str) -> tuple[str, ...]:
    return tuple(alias.lower() for alias in aliases)


SCENARIOS: tuple[CareerScenario, ...] = (
    CareerScenario(
        scenario_id="sim-log-hunt-token-reuse",
        title="Token Reuse in Authentication Logs",
        category="Log Hunt",
        difficulty="Intermediate",
        briefing=(
            "A synthetic enterprise identity service generated a small event set after a user "
            "reported an unexpected privileged action. Determine whether the events form a "
            "credible compromise chain and identify the strongest evidence."
        ),
        objectives=(
            "Identify the suspicious sequence rather than one isolated event.",
            "Separate evidence from assumptions.",
            "Recommend an immediate containment step and one detection improvement.",
        ),
        artifacts=(
            {
                "artifact_id": "auth.log",
                "title": "Identity events",
                "kind": "log",
                "content": (
                    "evt-1001 09:00 user=maya action=login result=success ip=10.0.4.18 device=corp-laptop-17 mfa=true\n"
                    "evt-1002 09:02 user=maya action=read_dashboard result=success ip=10.0.4.18 device=corp-laptop-17\n"
                    "evt-1040 09:41 user=maya action=login result=success ip=198.51.100.77 device=unknown mfa=false token_id=TKN-77\n"
                    "evt-1041 09:42 user=maya action=token_refresh result=success ip=198.51.100.77 device=unknown token_id=TKN-77\n"
                    "evt-1042 09:44 user=maya action=add_admin_role result=success ip=198.51.100.77 device=unknown token_id=TKN-77 target=svc-reports\n"
                    "evt-1043 09:46 user=maya action=export result=denied ip=198.51.100.77 device=unknown token_id=TKN-77 dataset=finance-q4\n"
                    "evt-1050 09:50 user=maya action=login result=success ip=10.0.4.18 device=corp-laptop-17 mfa=true\n"
                ),
            },
            {
                "artifact_id": "context.txt",
                "title": "Known context",
                "kind": "note",
                "content": (
                    "The employee states they were using corp-laptop-17 during the period. "
                    "The 198.51.100.0/24 range is reserved documentation space in this synthetic scenario. "
                    "No approved admin-role change was scheduled."
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="hunt-chain",
                title="Build the incident chain",
                prompt="Which event IDs form the strongest suspicious chain, and why?",
                answer_type="analysis",
                required_concepts=(
                    _concept("evt-1040"),
                    _concept("evt-1041"),
                    _concept("evt-1042"),
                    _concept("unknown device", "device=unknown"),
                    _concept("mfa=false", "no mfa", "without mfa"),
                    _concept("admin role", "add_admin_role", "privilege"),
                ),
                bonus_concepts=(
                    _concept("token_id=tkn-77", "tkn-77", "token reuse"),
                    _concept("evt-1043", "export denied"),
                    _concept("baseline", "corp-laptop-17", "normal login"),
                ),
                model_answer=(
                    "The strongest chain is evt-1040 → evt-1041 → evt-1042. Maya normally authenticates "
                    "from corp-laptop-17 with MFA, but evt-1040 shows a successful login from an unknown "
                    "device without MFA. The same TKN-77 is refreshed in evt-1041 and then used to add an "
                    "admin role in evt-1042 despite no approved change. evt-1043 adds supporting evidence "
                    "because the same token then attempts a sensitive export. I would treat TKN-77 as "
                    "compromised, revoke it, validate Maya's sessions, and create a correlation for new-device/"
                    "no-MFA authentication followed by privilege change."
                ),
                hints=(
                    "Compare the known-good login pattern with the later login.",
                    "Look for one identifier that connects multiple suspicious events.",
                    "Privilege change is stronger evidence than a strange IP alone.",
                ),
            ),
        ),
        skills=("SIEM", "identity telemetry", "incident triage", "correlation", "containment"),
    ),
    CareerScenario(
        scenario_id="sim-detection-rule-design",
        title="Design a Behavior-Based Detection",
        category="Detection Engineering",
        difficulty="Advanced",
        briefing=(
            "A synthetic application emits structured authorization events. A recent incident used "
            "a valid session to request a privileged action shortly after an untrusted document "
            "introduced an approval-looking string."
        ),
        objectives=(
            "Write behavior-oriented detection logic.",
            "Avoid naive string matching.",
            "Describe false-positive controls and required telemetry.",
        ),
        artifacts=(
            {
                "artifact_id": "events.ndjson",
                "title": "Authorization telemetry",
                "kind": "log",
                "content": (
                    '{"ts":"10:01:00","actor":"u-17","event":"context_loaded","source_trust":"untrusted","request_id":"r-9"}\n'
                    '{"ts":"10:01:03","actor":"u-17","event":"tool_requested","tool":"publish_report","request_id":"r-9","privileged":true}\n'
                    '{"ts":"10:01:03","actor":"u-17","event":"approval_checked","request_id":"r-9","approval_source":"none","approval_valid":false}\n'
                    '{"ts":"10:01:04","actor":"u-17","event":"tool_executed","tool":"publish_report","request_id":"r-9","result":"success"}\n'
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="detection-logic",
                title="Propose the detection",
                prompt=(
                    "Describe the detection condition, the fields you need, and at least two false-positive "
                    "controls. Do not rely on matching a specific prompt string."
                ),
                answer_type="design",
                required_concepts=(
                    _concept("approval_valid=false", "approval invalid", "invalid approval"),
                    _concept("tool_executed", "executed", "execution"),
                    _concept("privileged", "privileged tool", "sensitive tool"),
                    _concept("request_id", "same request", "correlate request"),
                    _concept("false positive", "false-positive"),
                    _concept("source_trust", "untrusted"),
                ),
                bonus_concepts=(
                    _concept("approval_source", "authorization source"),
                    _concept("allowlist", "expected automation", "service account"),
                    _concept("sequence", "eql", "esql", "kql", "correlation"),
                ),
                model_answer=(
                    "Correlate events by request_id and actor. Alert when a privileged tool is executed "
                    "successfully after approval_checked reports approval_valid=false or no trusted approval "
                    "source, especially when the same request consumed untrusted context. Required fields are "
                    "request_id, actor, tool, privileged, approval_valid, approval_source, source_trust, "
                    "execution result, and timestamp. False-positive controls should exclude explicitly "
                    "approved test/simulation identities and documented break-glass workflows, and should "
                    "verify that the executed action is truly privileged rather than every tool call."
                ),
                hints=(
                    "The interesting condition is a mismatch between authorization decision and execution.",
                    "Use request_id to create a sequence.",
                    "Ask which identities or workflows are intentionally allowed to behave differently.",
                ),
            ),
        ),
        skills=("detection-as-code", "correlation", "data requirements", "false-positive tuning"),
    ),
    CareerScenario(
        scenario_id="sim-dfir-scope",
        title="Scope a Synthetic Endpoint Incident",
        category="DFIR",
        difficulty="Advanced",
        briefing=(
            "A workstation produced a short synthetic process and network timeline. Determine the likely "
            "initial execution, persistence attempt, and scope-expansion evidence."
        ),
        objectives=("Build a timeline.", "Identify what is proven versus suspected.", "Prioritize containment."),
        artifacts=(
            {
                "artifact_id": "timeline.log",
                "title": "Endpoint timeline",
                "kind": "log",
                "content": (
                    "11:20:02 proc start parent=mailclient child=invoice_viewer.exe user=lee\n"
                    "11:20:06 file create path=C:/Users/lee/AppData/Local/Temp/aasl-demo.bin\n"
                    "11:20:09 proc start parent=invoice_viewer.exe child=script-host.exe args='demo-startup-registration'\n"
                    "11:20:11 registry write key=HKCU/Software/AASL/DemoRun value=script-host.exe\n"
                    "11:20:15 dns query process=script-host.exe name=telemetry.example.invalid\n"
                    "11:20:20 net connect process=script-host.exe dst=203.0.113.55:443 result=success\n"
                    "11:21:02 auth event user=lee target=fileserver result=success auth=existing-session\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="dfir-scope",
                title="Scope and contain",
                prompt="Summarize the timeline, identify the highest-confidence persistence evidence, and give your first three containment actions.",
                answer_type="analysis",
                required_concepts=(
                    _concept("invoice_viewer.exe", "invoice viewer"),
                    _concept("registry", "demorun", "persistence"),
                    _concept("script-host.exe", "script host"),
                    _concept("isolate", "isolation", "contain host"),
                    _concept("revoke", "session", "credential"),
                    _concept("preserve", "forensic", "evidence"),
                ),
                bonus_concepts=(
                    _concept("fileserver", "scope", "lateral"),
                    _concept("dns", "network", "203.0.113.55"),
                    _concept("mailclient", "initial execution"),
                ),
                model_answer=(
                    "The likely initial execution is mailclient → invoice_viewer.exe at 11:20:02. The strongest "
                    "persistence evidence is the registry write at 11:20:11 that points to script-host.exe. "
                    "The network connection and subsequent fileserver authentication indicate possible scope "
                    "expansion but do not prove compromise of the fileserver. First actions: isolate the "
                    "workstation, revoke/disable Lee's active sessions or tokens while preserving account "
                    "context, and preserve volatile/forensic evidence before remediation. Then review fileserver "
                    "access and search for the same registry/process/network indicators elsewhere."
                ),
                hints=(
                    "A registry persistence artifact is stronger than a suspicious process name.",
                    "Containment should reduce blast radius without destroying evidence.",
                    "The fileserver event is a pivot point, not proof of fileserver compromise.",
                ),
            ),
        ),
        skills=("timeline analysis", "containment", "forensic confidence", "scope expansion"),
    ),
    CareerScenario(
        scenario_id="sim-threat-intel-assessment",
        title="Assess a Synthetic Threat Campaign",
        category="Threat Intelligence",
        difficulty="Intermediate",
        briefing=(
            "You received a synthetic intelligence package with mixed-confidence indicators. Decide what is "
            "actionable, what needs validation, and how you would communicate confidence."
        ),
        objectives=("Prioritize intelligence.", "Use confidence language.", "Translate intel into action."),
        artifacts=(
            {
                "artifact_id": "intel.txt",
                "title": "Campaign notes",
                "kind": "intel",
                "content": (
                    "Source A (high reliability): three customers observed OAuth consent phishing followed by mailbox rule creation.\n"
                    "Source B (medium reliability): domain secure-login-aasl.example was registered 2 days before activity.\n"
                    "Source C (low reliability): social post claims group 'Night Kestrel' is responsible; no supporting evidence.\n"
                    "Observed TTPs: OAuth consent request, token use from new device, mailbox forwarding rule, archive download.\n"
                    "Known-good: company legitimately uses oauth-helper.aasl.example for internal testing.\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="intel-brief",
                title="Write the analytic judgment",
                prompt="Give a concise analytic judgment, confidence level, two defensive actions, and one thing you would not claim yet.",
                answer_type="analysis",
                required_concepts=(
                    _concept("oauth", "consent"),
                    _concept("mailbox", "forwarding rule"),
                    _concept("confidence", "moderate confidence", "high confidence"),
                    _concept("new device", "token"),
                    _concept("do not attribute", "attribution", "night kestrel"),
                    _concept("hunt", "detect", "monitor", "revoke"),
                ),
                bonus_concepts=(
                    _concept("source reliability", "source a", "source c"),
                    _concept("allowlist", "known-good", "oauth-helper"),
                    _concept("archive download", "collection"),
                ),
                model_answer=(
                    "I assess with moderate-to-high confidence that the campaign uses OAuth consent abuse to "
                    "obtain token-based access and establish mailbox forwarding, based on repeated observations "
                    "from the high-reliability source. I would hunt for new-device token use followed by mailbox "
                    "rule creation and review/revoke suspicious OAuth grants. I would explicitly exclude the "
                    "known-good oauth-helper test domain from blocking logic. I would not attribute the activity "
                    "to 'Night Kestrel' because that claim comes only from a low-reliability social source."
                ),
                hints=(
                    "Separate campaign behavior from actor attribution.",
                    "Use the source reliability labels.",
                    "A good intelligence product should drive a hunt or control change.",
                ),
            ),
        ),
        skills=("analytic confidence", "PIRs", "TTPs", "defensive action", "attribution discipline"),
    ),
    CareerScenario(
        scenario_id="sim-malware-behavior",
        title="Interpret a Synthetic Sandbox Trace",
        category="Malware Analysis",
        difficulty="Intermediate",
        briefing=(
            "A harmless synthetic specimen was executed in a local sandbox. Classify behaviors without "
            "assuming every suspicious action is malicious."
        ),
        objectives=("Classify persistence/network behavior.", "Distinguish evidence from intent.", "Propose signatures safely."),
        artifacts=(
            {
                "artifact_id": "sandbox.json",
                "title": "Sandbox behavior",
                "kind": "json",
                "content": json.dumps(
                    {
                        "sample": "invoice_viewer-demo.exe",
                        "processes": ["invoice_viewer-demo.exe", "script-host-demo.exe"],
                        "writes": ["C:/Users/demo/AppData/Local/Temp/aasl-marker.txt"],
                        "registry": ["HKCU/Software/AASL/DemoRun"],
                        "dns": ["beacon.example.invalid"],
                        "network": ["203.0.113.88:443"],
                        "notes": "No exploit or destructive action occurred. This is a synthetic trace.",
                    },
                    indent=2,
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="malware-classification",
                title="Classify behaviors",
                prompt="Identify the persistence and network behaviors, then propose two safe detection opportunities.",
                answer_type="analysis",
                required_concepts=(
                    _concept("registry", "demorun", "persistence"),
                    _concept("dns", "beacon.example.invalid"),
                    _concept("network", "203.0.113.88"),
                    _concept("process", "script-host-demo"),
                    _concept("detection", "detect"),
                ),
                bonus_concepts=(
                    _concept("yara", "static signature"),
                    _concept("behavior", "edr", "process tree"),
                    _concept("false positive", "baseline"),
                ),
                model_answer=(
                    "Persistence is represented by the DemoRun registry write. Network behavior is the DNS "
                    "lookup to beacon.example.invalid followed by a connection to 203.0.113.88:443. Safe "
                    "detections could correlate the invoice-viewer → script-host process tree with a new "
                    "autorun-style registry write, and separately alert on the synthetic domain/IP in the lab. "
                    "For production-quality detections I would prefer stable behavioral features over a single "
                    "filename and validate expected software before promoting the rule."
                ),
                hints=("Start with the registry key.", "Then correlate process lineage with outbound network activity."),
            ),
        ),
        skills=("sandbox analysis", "process trees", "persistence", "behavioral detection"),
    ),
    CareerScenario(
        scenario_id="sim-appsec-idor-review",
        title="Find the Authorization Defect",
        category="Application Security",
        difficulty="Intermediate",
        briefing=(
            "Review a deliberately simplified synthetic API handler. The goal is to identify the authorization "
            "boundary failure and describe a safe regression test."
        ),
        objectives=("Identify the root cause.", "Explain exploitability without attacking a real system.", "Propose a robust fix."),
        artifacts=(
            {
                "artifact_id": "handler.py",
                "title": "Synthetic API handler",
                "kind": "code",
                "content": (
                    "def get_invoice(request, invoice_id):\n"
                    "    user = authenticate(request)\n"
                    "    invoice = db.invoices.get(invoice_id)\n"
                    "    if not invoice:\n"
                    "        return 404\n"
                    "    return json_response(invoice)\n"
                ),
            },
            {
                "artifact_id": "schema.txt",
                "title": "Object ownership",
                "kind": "note",
                "content": "Invoice records include owner_user_id. Authentication is valid, but the handler does not compare owner_user_id with the authenticated user.",
            },
        ),
        tasks=(
            SimulationTask(
                task_id="appsec-root-cause",
                title="Find and fix the defect",
                prompt="Name the vulnerability class, explain the missing control, and describe the regression test you would add.",
                answer_type="analysis",
                required_concepts=(
                    _concept("idor", "broken object level authorization", "bola"),
                    _concept("owner_user_id", "ownership", "authorization check"),
                    _concept("authenticated user", "user id", "subject"),
                    _concept("403", "deny", "forbidden"),
                    _concept("regression test", "test"),
                ),
                bonus_concepts=(
                    _concept("server-side", "policy layer"),
                    _concept("object-level authorization", "resource authorization"),
                    _concept("enumeration", "guess id"),
                ),
                model_answer=(
                    "This is broken object-level authorization / IDOR. Authentication succeeds, but the handler "
                    "never verifies that invoice.owner_user_id matches the authenticated subject or another "
                    "explicit entitlement. The fix is a server-side authorization check (ideally centralized) "
                    "before returning the object. A regression test should create invoices owned by two users, "
                    "authenticate as User A, request User B's invoice ID, and assert the request is denied (for "
                    "example 403 or a non-enumerating 404 according to policy), while A can still access A's own invoice."
                ),
                hints=("Authentication and authorization are different.", "Look at owner_user_id in the schema note."),
            ),
        ),
        skills=("BOLA/IDOR", "authorization", "secure code review", "regression testing"),
    ),
    CareerScenario(
        scenario_id="sim-auth-bypass-toy",
        title="Bypass a Synthetic Role Gate",
        category="Adversary Simulation",
        difficulty="Advanced",
        briefing=(
            "A toy local API trusts a caller-controlled role header. Your task is to identify the bypass and "
            "state the safe proof you would use inside this synthetic environment."
        ),
        objectives=("Recognize a trust-boundary defect.", "Demonstrate impact safely.", "Recommend a durable fix."),
        artifacts=(
            {
                "artifact_id": "gateway.py",
                "title": "Toy authorization gate",
                "kind": "code",
                "content": (
                    "def authorize(request):\n"
                    "    session = verify_session(request.cookies.get('session'))\n"
                    "    requested_role = request.headers.get('X-Demo-Role', 'user')\n"
                    "    if session.valid and requested_role == 'admin':\n"
                    "        return True\n"
                    "    return False\n"
                ),
            },
            {
                "artifact_id": "scope.txt",
                "title": "Lab scope",
                "kind": "note",
                "content": "This is a synthetic local exercise. The only permitted proof is to explain or submit the toy header value; do not target any external service.",
            },
        ),
        tasks=(
            SimulationTask(
                task_id="bypass-analysis",
                title="Identify the bypass",
                prompt="What caller-controlled value creates the bypass, why is it unsafe, and what should the authorization decision trust instead?",
                answer_type="analysis",
                required_concepts=(
                    _concept("x-demo-role", "demo role"),
                    _concept("admin"),
                    _concept("caller-controlled", "header", "untrusted"),
                    _concept("server-side", "session claims", "trusted identity", "authorization policy"),
                ),
                bonus_concepts=(
                    _concept("tamper", "spoof"),
                    _concept("role claim", "entitlement"),
                    _concept("deny by default", "least privilege"),
                ),
                model_answer=(
                    "The bypass is the caller-controlled X-Demo-Role header. A valid low-privilege session can "
                    "supply X-Demo-Role: admin, and the gate treats that untrusted request metadata as authority. "
                    "The server should derive roles/entitlements from verified session or identity claims and "
                    "evaluate authorization against the requested resource/action, denying by default. The safe "
                    "lab proof is only to demonstrate the toy header behavior locally."
                ),
                hints=("Which authorization input can the client set directly?", "A valid session does not make every request header trustworthy."),
            ),
        ),
        skills=("authorization bypass", "trust boundaries", "adversary simulation", "secure remediation"),
    ),
    CareerScenario(
        scenario_id="sim-cloud-iam-review",
        title="Review an Over-Broad Cloud Policy",
        category="Cloud / IAM",
        difficulty="Intermediate",
        briefing="A synthetic workload policy is broader than the service needs. Reduce blast radius without breaking the documented function.",
        objectives=("Identify excessive privilege.", "Propose least-privilege scope.", "Consider workload identity."),
        artifacts=(
            {
                "artifact_id": "policy.json",
                "title": "Synthetic policy",
                "kind": "json",
                "content": json.dumps(
                    {
                        "Statement": [
                            {"Effect": "Allow", "Action": ["storage:*"], "Resource": "*"},
                            {"Effect": "Allow", "Action": ["kms:Decrypt"], "Resource": "*"},
                        ]
                    },
                    indent=2,
                ),
            },
            {
                "artifact_id": "requirements.txt",
                "title": "Workload requirement",
                "kind": "note",
                "content": "The reports service only needs to read objects from bucket aasl-reports/prod/* and decrypt them with key aasl-reports-key. It must not write or delete objects.",
            },
        ),
        tasks=(
            SimulationTask(
                task_id="iam-fix",
                title="Reduce privilege",
                prompt="Identify the two main over-privilege problems and describe the least-privilege replacement.",
                answer_type="design",
                required_concepts=(
                    _concept("storage:*", "wildcard action", "all storage actions"),
                    _concept("resource *", "resource wildcard", "resource=\"*\""),
                    _concept("read", "get object", "readonly"),
                    _concept("aasl-reports/prod", "reports/prod"),
                    _concept("aasl-reports-key", "specific key", "kms"),
                ),
                bonus_concepts=(
                    _concept("workload identity", "role", "short-lived"),
                    _concept("deny", "delete", "write"),
                    _concept("conditions", "scope"),
                ),
                model_answer=(
                    "The policy grants every storage action on every resource and KMS decrypt on every key. "
                    "The workload only needs read access to aasl-reports/prod/* and decrypt permission on "
                    "aasl-reports-key. Replace storage:* with the specific read action(s), scope the resource "
                    "to the reports prefix, and scope kms:Decrypt to the named key. Use workload identity or "
                    "a dedicated service role rather than long-lived shared credentials."
                ),
                hints=("Compare the policy verbs with the workload requirement.", "There are wildcards in both action and resource scope."),
            ),
        ),
        skills=("least privilege", "IAM", "KMS", "workload identity", "blast radius"),
    ),
    CareerScenario(
        scenario_id="sim-soar-playbook",
        title="Design a Safe SOAR Containment Playbook",
        category="Security Automation",
        difficulty="Advanced",
        briefing=(
            "A SOAR workflow can isolate endpoints automatically. Design the ordering so enrichment and "
            "decision quality happen before a potentially disruptive containment action."
        ),
        objectives=("Use safe ordering.", "Include approval/rollback.", "Make automation idempotent and observable."),
        artifacts=(
            {
                "artifact_id": "steps.txt",
                "title": "Available playbook actions",
                "kind": "note",
                "content": (
                    "A. isolate_endpoint\nB. enrich_asset_owner\nC. collect_alert_context\nD. notify_incident_channel\n"
                    "E. validate_severity_and_confidence\nF. create_case\nG. human_approval_for_high_business_impact\n"
                    "H. record_action_idempotency_key\nI. release_endpoint_if_false_positive\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="soar-order",
                title="Order the playbook",
                prompt="Describe a safe playbook sequence and the guardrails that prevent duplicate or harmful containment.",
                answer_type="design",
                required_concepts=(
                    _concept("collect", "context"),
                    _concept("enrich", "asset owner"),
                    _concept("validate", "severity", "confidence"),
                    _concept("approval", "human"),
                    _concept("isolate", "contain"),
                    _concept("idempotency", "idempotent", "duplicate"),
                    _concept("rollback", "release endpoint", "false positive"),
                ),
                bonus_concepts=(
                    _concept("case", "create_case"),
                    _concept("notify", "incident channel"),
                    _concept("audit", "record", "observability"),
                ),
                model_answer=(
                    "Collect alert context and enrich asset/business ownership first, then validate severity and "
                    "confidence. Create/update the case and, for high-business-impact assets, require human "
                    "approval before isolation. Record an idempotency key before the containment action so "
                    "retries do not isolate repeatedly. Notify responders with the action result and preserve "
                    "an explicit rollback/release step for a confirmed false positive."
                ),
                hints=("Containment is disruptive; don't make it the first step.", "How will retries behave?", "Every automated action needs a reversal story."),
            ),
        ),
        skills=("SOAR", "playbook design", "idempotency", "human approval", "rollback"),
    ),
    CareerScenario(
        scenario_id="sim-sensitive-data-discovery",
        title="Find Synthetic Sensitive Data",
        category="Data Discovery",
        difficulty="Intermediate",
        briefing=(
            "A synthetic repository contains several files. Use the Career Lab search workbench to identify "
            "the files that should not contain sensitive material and propose a safer control."
        ),
        objectives=("Use a basic search strategy.", "Separate real findings from harmless placeholders.", "Recommend prevention."),
        artifacts=(
            {
                "artifact_id": "repo-files.txt",
                "title": "Synthetic repository contents",
                "kind": "files",
                "content": (
                    "config/dev.env: API_TOKEN=AASL_DEMO_TOKEN_8F3A2\n"
                    "docs/example.env: API_TOKEN=YOUR_TOKEN_HERE\n"
                    "fixtures/patient.json: {\"name\":\"Test Patient\",\"mrn\":\"AASL-00017\",\"email\":\"test.patient@example.invalid\"}\n"
                    "src/settings.py: TOKEN_ENV_VAR='API_TOKEN'\n"
                    "README.md: Use a secret manager for production credentials.\n"
                    "logs/debug.log: Authorization: Bearer AASL_DEMO_BEARER_71C9\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="sensitive-search",
                title="Create a basic search and classify findings",
                prompt=(
                    "Describe the search pattern/tool you would use, identify the sensitive-looking files, "
                    "and explain which value is only a placeholder."
                ),
                answer_type="tooling",
                required_concepts=(
                    _concept("api_token", "token", "bearer", "authorization"),
                    _concept("config/dev.env", "dev.env"),
                    _concept("logs/debug.log", "debug.log"),
                    _concept("fixtures/patient.json", "patient.json", "mrn"),
                    _concept("docs/example.env", "your_token_here", "placeholder"),
                ),
                bonus_concepts=(
                    _concept("regex", "grep", "ripgrep", "search"),
                    _concept("secret manager", "secrets manager"),
                    _concept("pre-commit", "secret scanning", "ci"),
                ),
                model_answer=(
                    "I would start with a simple repository search for credential markers such as API_TOKEN, "
                    "Authorization: Bearer, token-like prefixes, and sensitive-data fields such as MRN/email, "
                    "then inspect context rather than treating every match as a secret. The sensitive-looking "
                    "locations are config/dev.env (demo token), logs/debug.log (bearer value), and "
                    "fixtures/patient.json (synthetic patient identifiers). docs/example.env contains "
                    "YOUR_TOKEN_HERE, which is only a placeholder. Prevention should include secret scanning "
                    "in pre-commit/CI, log redaction, test-only synthetic datasets, and a secret manager."
                ),
                hints=(
                    "Use the workbench search for TOKEN, Bearer, MRN, and email.",
                    "Not every match is a secret; inspect the actual value.",
                    "Think about preventing both repository secrets and sensitive logging.",
                ),
            ),
        ),
        skills=("secret discovery", "data classification", "search tooling", "preventive controls"),
    ),
    CareerScenario(
        scenario_id="sim-vuln-prioritization",
        title="Prioritize Vulnerabilities by Exposure",
        category="Vulnerability Management",
        difficulty="Intermediate",
        briefing="Three synthetic findings have different severity and exposure. Decide what to fix first and justify the ordering.",
        objectives=("Prioritize beyond CVSS.", "Use exploitability and asset criticality.", "Define an SLA."),
        artifacts=(
            {
                "artifact_id": "findings.csv",
                "title": "Synthetic vulnerability queue",
                "kind": "table",
                "content": (
                    "ID,CVSS,InternetExposed,KnownExploit,Asset,Criticality\n"
                    "V-101,9.8,false,false,dev-build-runner,medium\n"
                    "V-102,8.1,true,true,customer-auth-api,critical\n"
                    "V-103,9.1,true,false,marketing-cms,low\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="vuln-priority",
                title="Rank the queue",
                prompt="Rank V-101, V-102, and V-103 and explain the factors that matter more than CVSS alone.",
                answer_type="analysis",
                required_concepts=(
                    _concept("v-102"),
                    _concept("known exploit", "exploited", "exploitability"),
                    _concept("internet", "exposed"),
                    _concept("critical", "customer-auth-api"),
                    _concept("asset criticality", "business impact"),
                ),
                bonus_concepts=(
                    _concept("v-103"),
                    _concept("v-101"),
                    _concept("sla", "remediation"),
                ),
                model_answer=(
                    "V-102 is first despite the lower CVSS because it is internet exposed, has a known exploit, "
                    "and affects the critical customer authentication API. I would place V-103 second because it "
                    "is internet exposed but has lower asset criticality and no known exploit in the scenario. "
                    "V-101 is third because it is not internet exposed and affects a medium-criticality dev runner. "
                    "The remediation SLA should reflect exposure, exploitability, and business criticality rather than CVSS alone."
                ),
                hints=("Which finding combines exploitability, exposure, and a critical asset?",),
            ),
        ),
        skills=("risk-based prioritization", "asset context", "exploitability", "remediation SLA"),
    ),
    CareerScenario(
        scenario_id="sim-security-architecture",
        title="Review an Agentic Trust Boundary",
        category="Security Architecture",
        difficulty="Advanced",
        briefing=(
            "A synthetic agent design sends retrieved documents, a user token, and tool calls through one "
            "shared orchestration context. Identify trust boundaries and propose a safer architecture."
        ),
        objectives=("Identify trust domains.", "Separate data from authority.", "Design least-privilege identities."),
        artifacts=(
            {
                "artifact_id": "architecture.txt",
                "title": "Current design",
                "kind": "diagram",
                "content": (
                    "User -> Web App -> Orchestrator\n"
                    "Orchestrator context contains: user prompt + retrieved documents + user bearer token\n"
                    "Orchestrator -> Search Tool\n"
                    "Orchestrator -> Publish Tool (same token)\n"
                    "Sub-agent receives full orchestrator context including bearer token\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="architecture-redesign",
                title="Redesign trust boundaries",
                prompt="Identify at least three security problems and describe the safer identity/authorization architecture.",
                answer_type="design",
                required_concepts=(
                    _concept("untrusted", "retrieved documents", "data not authority"),
                    _concept("token", "credential", "bearer"),
                    _concept("sub-agent", "credential propagation", "child"),
                    _concept("least privilege", "scoped credential", "derived"),
                    _concept("tool authorization", "approval", "policy"),
                    _concept("separate", "trust boundary"),
                ),
                bonus_concepts=(
                    _concept("audience", "resource", "request"),
                    _concept("provenance", "taint"),
                    _concept("audit", "telemetry"),
                ),
                model_answer=(
                    "The design mixes untrusted retrieved data with authority, puts a reusable bearer token in "
                    "the orchestration context, gives both tools the same credential, and propagates that token "
                    "to a sub-agent. I would keep retrieved content as explicitly untrusted data, evaluate each "
                    "privileged tool action at a policy boundary, use per-tool/workload identities or derived "
                    "short-lived credentials scoped to subject/audience/action/resource/request, and never "
                    "propagate the parent credential into a child agent by default. Log the delegation and "
                    "authorization decisions with provenance."
                ),
                hints=("Ask what data is untrusted and what grants authority.", "Why should Search and Publish share the same credential?", "What should a sub-agent inherit by default?"),
            ),
        ),
        skills=("trust boundaries", "identity", "tool authorization", "credential scope", "agent architecture"),
    ),
    CareerScenario(
        scenario_id="sim-grc-exception",
        title="Decide a Security Exception",
        category="Risk / Governance",
        difficulty="Advanced",
        briefing=(
            "A critical product launch cannot meet one control by the release date. Make a defensible risk "
            "decision with compensating controls, ownership, and expiration."
        ),
        objectives=("Make a risk-based decision.", "Define compensating controls.", "Avoid permanent exceptions."),
        artifacts=(
            {
                "artifact_id": "exception.txt",
                "title": "Launch context",
                "kind": "note",
                "content": (
                    "Launch date: Friday.\n"
                    "Missing control: production service-account key rotation automation.\n"
                    "Current keys are 20 days old; policy target is automated 30-day rotation.\n"
                    "Service supports manual rotation and dual-key overlap.\n"
                    "Business impact of delaying launch: high.\n"
                    "Engineering can finish automation in 3 weeks.\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="grc-decision",
                title="Approve, deny, or conditionally accept",
                prompt="State your decision and the controls, owner, evidence, and expiration you would require.",
                answer_type="decision",
                required_concepts=(
                    _concept("conditional", "temporary", "exception"),
                    _concept("manual rotation", "rotate"),
                    _concept("owner", "accountable"),
                    _concept("expiration", "expiry", "3 weeks", "time-bound"),
                    _concept("evidence", "verify", "monitor"),
                ),
                bonus_concepts=(
                    _concept("dual-key", "overlap"),
                    _concept("risk acceptance", "business owner"),
                    _concept("follow-up", "automation"),
                ),
                model_answer=(
                    "I would consider a time-bound conditional exception rather than a permanent waiver, because "
                    "the current keys are still within the 30-day target and a manual control exists. Before launch "
                    "I would require documented manual rotation using dual-key overlap, assign a named engineering "
                    "owner, capture evidence of the rotation and monitoring, and set the exception to expire when "
                    "automation is due in three weeks (or earlier). The accountable business/security owner should "
                    "accept the residual risk, and the launch should be blocked if the compensating control is not executed."
                ),
                hints=("An exception should have an owner and an end date.", "Use the manual capability as a compensating control if it is actually executed."),
            ),
        ),
        skills=("risk acceptance", "exceptions", "compensating controls", "governance", "business tradeoffs"),
    ),
    CareerScenario(
        scenario_id="sim-crypto-config",
        title="Review a Synthetic Crypto Configuration",
        category="Cryptography",
        difficulty="Intermediate",
        briefing="Review a synthetic transport/key configuration and identify modernization priorities.",
        objectives=("Spot weak configuration.", "Prioritize protocol and key lifecycle.", "Avoid inventing guarantees."),
        artifacts=(
            {
                "artifact_id": "crypto.conf",
                "title": "Synthetic configuration",
                "kind": "config",
                "content": (
                    "min_tls_version = TLS1.0\n"
                    "certificate_key_bits = 1024\n"
                    "key_rotation_days = 365\n"
                    "private_key_storage = application_config_file\n"
                    "certificate_validation = enabled\n"
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="crypto-review",
                title="Prioritize crypto remediation",
                prompt="Identify the highest-priority issues and describe a safer target state.",
                answer_type="analysis",
                required_concepts=(
                    _concept("tls1.0", "tls 1.0", "protocol"),
                    _concept("1024", "key size"),
                    _concept("private key", "config file", "key storage"),
                    _concept("rotation", "365"),
                    _concept("kms", "hsm", "secure key storage", "managed key"),
                ),
                bonus_concepts=(
                    _concept("tls1.2", "tls 1.2", "tls1.3", "tls 1.3"),
                    _concept("inventory", "compatibility"),
                    _concept("certificate validation"),
                ),
                model_answer=(
                    "The priorities are removing TLS 1.0, replacing the 1024-bit key with an approved modern "
                    "key size/algorithm according to organizational policy, moving private keys out of application "
                    "configuration into managed protected storage such as KMS/HSM or an equivalent secret/key "
                    "service, and shortening/automating the rotation lifecycle. Certificate validation is already "
                    "enabled and should remain so. Migration should include dependency inventory and compatibility testing."
                ),
                hints=("Look at protocol age, key strength, key storage, and lifecycle separately.",),
            ),
        ),
        skills=("TLS", "key management", "rotation", "secure storage", "migration"),
    ),
    CareerScenario(
        scenario_id="sim-ai-agent-boundary",
        title="Investigate an Agent Authorization Failure",
        category="AI / Agentic Security",
        difficulty="Expert",
        briefing=(
            "A synthetic agent consumed untrusted retrieval context and then executed a privileged tool. "
            "Use the trace to determine whether this is prompt injection alone or an authorization-boundary failure."
        ),
        objectives=("Separate model behavior from authorization.", "Identify the decisive control failure.", "Recommend architecture and detection controls."),
        artifacts=(
            {
                "artifact_id": "agent-trace.ndjson",
                "title": "Agent trace",
                "kind": "log",
                "content": (
                    '{"event":"retrieve","source":"external-note","trust":"untrusted","request_id":"r-77"}\n'
                    '{"event":"model_plan","text":"publish summary","request_id":"r-77"}\n'
                    '{"event":"tool_request","tool":"publish_report","privileged":true,"request_id":"r-77"}\n'
                    '{"event":"approval","source":"retrieved_context","valid":false,"request_id":"r-77"}\n'
                    '{"event":"tool_execute","tool":"publish_report","result":"success","request_id":"r-77"}\n'
                ),
            },
        ),
        tasks=(
            SimulationTask(
                task_id="ai-boundary",
                title="Find the real security failure",
                prompt="Explain the root security failure, the evidence chain, and one preventive plus one detective control.",
                answer_type="analysis",
                required_concepts=(
                    _concept("authorization", "approval"),
                    _concept("untrusted", "retrieved context"),
                    _concept("valid=false", "invalid approval"),
                    _concept("tool_execute", "executed", "success"),
                    _concept("prevent", "policy", "trusted approval"),
                    _concept("detect", "correlate", "alert"),
                ),
                bonus_concepts=(
                    _concept("request_id", "r-77"),
                    _concept("prompt injection", "model behavior"),
                    _concept("least privilege", "tool boundary"),
                ),
                model_answer=(
                    "The decisive failure is not merely that untrusted retrieval influenced the model plan; it is "
                    "that the privileged tool executed even though the approval event was sourced from retrieved "
                    "context and explicitly invalid. Correlating request r-77 shows untrusted retrieval → tool request "
                    "→ invalid approval → successful privileged execution. Preventively, privileged tools should "
                    "require a trusted exact-action authorization source independent of model/retrieval content. "
                    "Detectively, alert on privileged execution when the correlated approval is missing/invalid or "
                    "comes from an untrusted source."
                ),
                hints=("A model can propose a bad action without the system being exploitable.", "Look for the enforcement decision immediately before execution."),
            ),
        ),
        skills=("prompt injection", "tool authorization", "provenance", "agent telemetry", "detection"),
    ),
)


SCENARIO_OWASP: dict[str, dict[str, tuple[dict[str, str], ...]]] = {
    "sim-log-hunt-token-reuse": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A07:2025", "name": "Authentication Failures"},
            {"id": "A09:2025", "name": "Security Logging and Alerting Failures"},
        ),
    },
    "sim-detection-rule-design": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A09:2025", "name": "Security Logging and Alerting Failures"},
        ),
        "owasp_llm": (
            {"id": "LLM03:2026", "name": "Excessive Agency"},
        ),
        "owasp_agentic": (
            {"id": "ASI02", "name": "Tool Misuse and Exploitation"},
            {"id": "ASI03", "name": "Identity and Privilege Abuse"},
        ),
    },
    "sim-dfir-scope": {
        "owasp_web": (
            {"id": "A09:2025", "name": "Security Logging and Alerting Failures"},
        ),
    },
    "sim-threat-intel-assessment": {},
    "sim-malware-behavior": {},
    "sim-appsec-idor-review": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A06:2025", "name": "Insecure Design"},
        ),
    },
    "sim-auth-bypass-toy": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A06:2025", "name": "Insecure Design"},
            {"id": "A07:2025", "name": "Authentication Failures"},
        ),
    },
    "sim-cloud-iam-review": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A02:2025", "name": "Security Misconfiguration"},
            {"id": "A04:2025", "name": "Cryptographic Failures"},
        ),
    },
    "sim-soar-playbook": {
        "owasp_web": (
            {"id": "A06:2025", "name": "Insecure Design"},
            {"id": "A10:2025", "name": "Mishandling of Exceptional Conditions"},
        ),
    },
    "sim-sensitive-data-discovery": {
        "owasp_web": (
            {"id": "A02:2025", "name": "Security Misconfiguration"},
            {"id": "A09:2025", "name": "Security Logging and Alerting Failures"},
        ),
        "owasp_llm": (
            {"id": "LLM02:2026", "name": "Sensitive Information Disclosure"},
        ),
        "owasp_agentic": (
            {"id": "ASI03", "name": "Identity and Privilege Abuse"},
        ),
    },
    "sim-vuln-prioritization": {
        "owasp_web": (
            {"id": "A03:2025", "name": "Software Supply Chain Failures"},
            {"id": "A06:2025", "name": "Insecure Design"},
        ),
    },
    "sim-security-architecture": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A06:2025", "name": "Insecure Design"},
        ),
        "owasp_llm": (
            {"id": "LLM03:2026", "name": "Excessive Agency"},
            {"id": "LLM02:2026", "name": "Sensitive Information Disclosure"},
        ),
        "owasp_agentic": (
            {"id": "ASI02", "name": "Tool Misuse and Exploitation"},
            {"id": "ASI03", "name": "Identity and Privilege Abuse"},
            {"id": "ASI06", "name": "Memory and Context Poisoning"},
        ),
    },
    "sim-grc-exception": {
        "owasp_web": (
            {"id": "A06:2025", "name": "Insecure Design"},
        ),
    },
    "sim-crypto-config": {
        "owasp_web": (
            {"id": "A04:2025", "name": "Cryptographic Failures"},
            {"id": "A02:2025", "name": "Security Misconfiguration"},
        ),
    },
    "sim-ai-agent-boundary": {
        "owasp_web": (
            {"id": "A01:2025", "name": "Broken Access Control"},
            {"id": "A06:2025", "name": "Insecure Design"},
            {"id": "A09:2025", "name": "Security Logging and Alerting Failures"},
        ),
        "owasp_llm": (
            {"id": "LLM01:2026", "name": "Prompt Injection"},
            {"id": "LLM03:2026", "name": "Excessive Agency"},
        ),
        "owasp_agentic": (
            {"id": "ASI01", "name": "Agent Goal Hijack"},
            {"id": "ASI02", "name": "Tool Misuse and Exploitation"},
            {"id": "ASI03", "name": "Identity and Privilege Abuse"},
        ),
    },
}


SCENARIO_RUNTIME: dict[str, dict[str, Any]] = {
    "sim-log-hunt-token-reuse": {"tier": "vm-optional", "blueprint_id": "linux-soc-dfir"},
    "sim-detection-rule-design": {"tier": "inline", "blueprint_id": "linux-soc-dfir"},
    "sim-dfir-scope": {"tier": "vm-recommended", "blueprint_id": "linux-soc-dfir"},
    "sim-threat-intel-assessment": {"tier": "inline", "blueprint_id": None},
    "sim-malware-behavior": {"tier": "vm-recommended", "blueprint_id": "linux-soc-dfir"},
    "sim-appsec-idor-review": {"tier": "vm-optional", "blueprint_id": "linux-appsec"},
    "sim-auth-bypass-toy": {"tier": "vm-optional", "blueprint_id": "linux-appsec"},
    "sim-cloud-iam-review": {"tier": "vm-optional", "blueprint_id": "linux-cloud-iam"},
    "sim-soar-playbook": {"tier": "inline", "blueprint_id": "linux-cloud-iam"},
    "sim-sensitive-data-discovery": {"tier": "vm-recommended", "blueprint_id": "linux-appsec"},
    "sim-vuln-prioritization": {"tier": "inline", "blueprint_id": None},
    "sim-security-architecture": {"tier": "inline", "blueprint_id": "linux-cloud-iam"},
    "sim-grc-exception": {"tier": "inline", "blueprint_id": "linux-cloud-iam"},
    "sim-crypto-config": {"tier": "vm-optional", "blueprint_id": "linux-cloud-iam"},
    "sim-ai-agent-boundary": {"tier": "vm-recommended", "blueprint_id": "linux-cloud-iam"},
}


SCENARIO_ATLAS: dict[str, tuple[dict[str, str], ...]] = {
    "sim-ai-agent-boundary": (
        {"id": "AML.T0051", "name": "LLM Prompt Injection", "tactic": "Execution"},
        {"id": "AML.T0053", "name": "AI Agent Tool Invocation", "tactic": "Execution / Privilege Escalation"},
    ),
    "sim-detection-rule-design": (
        {"id": "AML.T0053", "name": "AI Agent Tool Invocation", "tactic": "Execution / Privilege Escalation"},
    ),
    "sim-sensitive-data-discovery": (
        {"id": "AML.T0057", "name": "LLM Data Leakage", "tactic": "Exfiltration"},
        {"id": "AML.T0098", "name": "AI Agent Tool Credential Harvesting", "tactic": "Credential Access"},
    ),
    "sim-security-architecture": (
        {"id": "AML.T0084", "name": "Discover AI Agent Configuration", "tactic": "Discovery"},
        {"id": "AML.T0133", "name": "Discover AI Agent Runtime Capabilities", "tactic": "Discovery"},
        {"id": "AML.T0053", "name": "AI Agent Tool Invocation", "tactic": "Execution / Privilege Escalation"},
    ),
}


ATLAS_SPECIALIZATION: tuple[dict[str, str], ...] = (
    {"id": "AML.T0051", "name": "LLM Prompt Injection", "platform": "Generative AI / Agentic AI"},
    {"id": "AML.T0070", "name": "RAG Poisoning", "platform": "Generative AI / Agentic AI"},
    {"id": "AML.T0053", "name": "AI Agent Tool Invocation", "platform": "Agentic AI"},
    {"id": "AML.T0098", "name": "AI Agent Tool Credential Harvesting", "platform": "Agentic AI"},
    {"id": "AML.T0083", "name": "Credentials from AI Agent Configuration", "platform": "Agentic AI"},
    {"id": "AML.T0084", "name": "Discover AI Agent Configuration", "platform": "Agentic AI"},
    {"id": "AML.T0133", "name": "Discover AI Agent Runtime Capabilities", "platform": "Agentic AI"},
    {"id": "AML.T0081", "name": "Modify AI Agent Configuration", "platform": "Agentic AI"},
    {"id": "AML.T0086", "name": "Exfiltration via AI Agent Tool Invocation", "platform": "Agentic AI"},
    {"id": "AML.T0056", "name": "Extract LLM System Prompt", "platform": "Generative AI / Agentic AI"},
    {"id": "AML.T0057", "name": "LLM Data Leakage", "platform": "Generative AI / Agentic AI"},
    {"id": "AML.T0100", "name": "AI Agent Clickbait", "platform": "Agentic AI"},
    {"id": "AML.T0110", "name": "AI Agent Tool Poisoning", "platform": "Agentic AI"},
    {"id": "AML.T0099", "name": "AI Agent Tool Data Poisoning", "platform": "Agentic AI"},
    {"id": "AML.T0118", "name": "Autonomous AI Agent Communication", "platform": "Agentic AI / Enterprise"},
    {"id": "AML.T0117", "name": "Autonomous Attack-Path Adaptation", "platform": "Agentic AI"},
    {"id": "AML.T0124", "name": "Autonomous Attack Orchestration", "platform": "Agentic AI"},
)


ROLE_SCENARIOS: dict[str, tuple[str, ...]] = {
    "soc-analyst": ("sim-log-hunt-token-reuse", "sim-dfir-scope", "sim-soar-playbook"),
    "detection-engineer": ("sim-detection-rule-design", "sim-log-hunt-token-reuse", "sim-ai-agent-boundary"),
    "threat-hunter": ("sim-log-hunt-token-reuse", "sim-threat-intel-assessment", "sim-dfir-scope"),
    "incident-response-dfir": ("sim-dfir-scope", "sim-log-hunt-token-reuse", "sim-malware-behavior"),
    "threat-intel": ("sim-threat-intel-assessment", "sim-log-hunt-token-reuse"),
    "malware-analysis": ("sim-malware-behavior", "sim-dfir-scope"),
    "red-team": ("sim-auth-bypass-toy", "sim-ai-agent-boundary", "sim-cloud-iam-review"),
    "penetration-testing": ("sim-auth-bypass-toy", "sim-appsec-idor-review", "sim-cloud-iam-review"),
    "purple-team": ("sim-detection-rule-design", "sim-auth-bypass-toy", "sim-log-hunt-token-reuse"),
    "vulnerability-management": ("sim-vuln-prioritization", "sim-appsec-idor-review"),
    "appsec": ("sim-appsec-idor-review", "sim-sensitive-data-discovery", "sim-auth-bypass-toy"),
    "product-security": ("sim-appsec-idor-review", "sim-security-architecture", "sim-sensitive-data-discovery"),
    "cloud-security": ("sim-cloud-iam-review", "sim-sensitive-data-discovery", "sim-security-architecture"),
    "devsecops": ("sim-sensitive-data-discovery", "sim-cloud-iam-review", "sim-soar-playbook"),
    "security-architecture": ("sim-security-architecture", "sim-cloud-iam-review", "sim-ai-agent-boundary"),
    "soar-security-automation": ("sim-soar-playbook", "sim-log-hunt-token-reuse"),
    "iam": ("sim-cloud-iam-review", "sim-auth-bypass-toy", "sim-security-architecture"),
    "network-security": ("sim-log-hunt-token-reuse", "sim-dfir-scope", "sim-malware-behavior"),
    "endpoint-security": ("sim-dfir-scope", "sim-malware-behavior", "sim-detection-rule-design"),
    "grc-risk": ("sim-grc-exception", "sim-vuln-prioritization", "sim-security-architecture"),
    "security-program": ("sim-grc-exception", "sim-vuln-prioritization", "sim-soar-playbook"),
    "security-leadership": ("sim-grc-exception", "sim-security-architecture", "sim-vuln-prioritization"),
    "supply-chain-security": ("sim-sensitive-data-discovery", "sim-vuln-prioritization", "sim-grc-exception"),
    "ai-security": ("sim-ai-agent-boundary", "sim-security-architecture", "sim-auth-bypass-toy", "sim-detection-rule-design"),
    "security-research": ("sim-ai-agent-boundary", "sim-auth-bypass-toy", "sim-malware-behavior"),
    "cryptography": ("sim-crypto-config", "sim-security-architecture"),
}


DIMENSION_GUIDANCE: dict[str, dict[str, Any]] = {
    "Technical depth": {
        "required": (_concept("principle", "control", "failure"), _concept("production", "operational")),
        "model": "Define the security principle, explain how the control works, identify realistic failure modes, and distinguish design intent from production evidence.",
    },
    "Architecture": {
        "required": (_concept("trust boundary", "boundary"), _concept("identity", "authorization"), _concept("telemetry", "logging"), _concept("failure", "fallback")),
        "model": "State the trust boundaries, identities, authorization decisions, telemetry, data flows, failure modes, and least-privilege control points. Explain what is enforced where.",
    },
    "Adversarial scenario": {
        "required": (_concept("triage"), _concept("contain", "containment"), _concept("evidence"), _concept("scope"), _concept("decision")),
        "model": "Triage confidence and blast radius, preserve evidence, contain the highest-risk path, scope adjacent systems, make an explicit risk decision, and define recovery/validation criteria.",
    },
    "Proactive security": {
        "required": (_concept("baseline", "inventory"), _concept("threat model", "risk"), _concept("prevent", "guardrail"), _concept("detect", "telemetry"), _concept("measure", "metric")),
        "model": "Start with inventory/baseline and threat modeling, then prioritize preventive guardrails, required telemetry/detections, validation exercises, ownership, and measurable risk-reduction outcomes.",
    },
    "Metrics": {
        "required": (_concept("coverage"), _concept("time", "mttr", "mttd"), _concept("risk", "severity"), _concept("quality", "false positive", "precision")),
        "model": "Use outcome metrics: coverage of high-risk behaviors/assets, detection/response time, control failure or exposure reduction, and quality metrics such as false-positive rate or validation pass rate.",
    },
    "Hands-on": {
        "required": (_concept("personally", "implemented", "built"), _concept("result", "outcome"), _concept("measure", "metric")),
        "model": "Describe what you personally built or changed, the technical mechanism, how you validated it, and the measurable before/after outcome.",
    },
    "Tradeoffs": {
        "required": (_concept("risk"), _concept("business"), _concept("compensating", "mitigation"), _concept("owner", "accept"), _concept("time-bound", "expiry", "deadline")),
        "model": "Frame business value and security risk, identify compensating controls and residual risk, assign an accountable owner, set explicit acceptance criteria and expiration, and revisit after the constraint changes.",
    },
    "Behavioral / influence": {
        "required": (_concept("stakeholder"), _concept("evidence", "data"), _concept("tradeoff"), _concept("outcome")),
        "model": "Explain the disagreement, stakeholder incentives, evidence you used, options/tradeoffs you presented, the decision process, and the concrete outcome while preserving the relationship.",
    },
    "Scale": {
        "required": (_concept("12-month", "roadmap", "phases"), _concept("operating model"), _concept("staff", "team"), _concept("budget", "funding"), _concept("metrics", "executive")),
        "model": "Build a phased 12-month roadmap with operating model, ownership, staffing/skills, platform investment, measurable milestones, dependencies, and executive risk reporting.",
    },
    "Leadership": {
        "required": (_concept("own", "ownership"), _concept("federate", "embedded", "engineering"), _concept("standards", "guardrail"), _concept("accountability")),
        "model": "Centralize standards, high-risk decisions, shared platforms, and independent assurance; federate implementation where domain teams have context; define clear accountability and escalation boundaries.",
    },
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _matches(answer: str, aliases: tuple[str, ...]) -> bool:
    normalized = _normalize(answer)
    return any(alias in normalized for alias in aliases)


def _grade(
    answer: str,
    required: tuple[tuple[str, ...], ...],
    bonus: tuple[tuple[str, ...], ...] = (),
) -> dict[str, Any]:
    answer = answer.strip()
    if not answer:
        return {
            "score": 0,
            "matched": [],
            "missing": [group[0] for group in required],
            "bonus_matched": [],
            "quality": "No answer submitted",
        }

    matched = [group[0] for group in required if _matches(answer, group)]
    missing = [group[0] for group in required if not _matches(answer, group)]
    bonus_matched = [group[0] for group in bonus if _matches(answer, group)]

    required_score = 80 * (len(matched) / max(1, len(required)))
    bonus_score = 20 * (len(bonus_matched) / max(1, len(bonus))) if bonus else 0
    length_bonus = min(8, max(0, (len(answer.split()) - 35) / 15))
    score = min(100, round(required_score + bonus_score + length_bonus))

    if score >= 90:
        quality = "Excellent"
    elif score >= 75:
        quality = "Strong"
    elif score >= 60:
        quality = "Developing"
    else:
        quality = "Needs more depth"

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "bonus_matched": bonus_matched,
        "quality": quality,
    }


def career_simulation_catalog(role_id: str | None = None) -> dict[str, Any]:
    scenarios = {scenario.scenario_id: scenario for scenario in SCENARIOS}
    if role_id:
        ids = ROLE_SCENARIOS.get(role_id, ())
        selected = [scenarios[sid] for sid in ids if sid in scenarios]
    else:
        selected = list(SCENARIOS)
    rows = []
    for scenario in selected:
        row = asdict(scenario)
        row["runtime"] = SCENARIO_RUNTIME.get(
            scenario.scenario_id,
            {"tier": "inline", "blueprint_id": None},
        )
        row["atlas"] = list(SCENARIO_ATLAS.get(scenario.scenario_id, ()))
        owasp = SCENARIO_OWASP.get(scenario.scenario_id, {})
        row["owasp_web"] = list(owasp.get("owasp_web", ()))
        row["owasp_llm"] = list(owasp.get("owasp_llm", ()))
        row["owasp_agentic"] = list(owasp.get("owasp_agentic", ()))
        row["specialization"] = (
            "AI / Agentic Security Specialization"
            if row["atlas"] or row["owasp_llm"] or row["owasp_agentic"]
            else "Core Cybersecurity"
        )
        rows.append(row)
    return {
        "role_id": role_id,
        "scenarios": rows,
        "total_scenarios": len(SCENARIOS),
        "atlas_specialization": list(ATLAS_SPECIALIZATION),
        "frameworks": framework_catalog(),
    }


def evaluate_simulation_task(
    scenario_id: str,
    task_id: str,
    answer: str,
    hints_used: int = 0,
) -> dict[str, Any]:
    scenario = next((s for s in SCENARIOS if s.scenario_id == scenario_id), None)
    if scenario is None:
        raise ValueError(f"unknown scenario: {scenario_id}")
    task = next((t for t in scenario.tasks if t.task_id == task_id), None)
    if task is None:
        raise ValueError(f"unknown task: {task_id}")

    grade = _grade(answer, task.required_concepts, task.bonus_concepts)
    hint_penalty = min(15, max(0, hints_used) * 5)
    adjusted = max(0, grade["score"] - hint_penalty)

    strengths = [f"Covered: {concept}" for concept in grade["matched"][:5]]
    if grade["bonus_matched"]:
        strengths.append("Added useful depth: " + ", ".join(grade["bonus_matched"][:3]))
    improvements = [f"Add explicit discussion of {concept}." for concept in grade["missing"][:5]]
    if hints_used:
        improvements.append(
            f"You used {hints_used} hint(s). Re-run the scenario without hints to test independent recall."
        )
    if not improvements:
        improvements.append("The answer covers the expected core points; improve concision and evidence ordering if needed.")

    return {
        "scenario_id": scenario_id,
        "task_id": task_id,
        "score": adjusted,
        "raw_score": grade["score"],
        "hint_penalty": hint_penalty,
        "quality": grade["quality"] if adjusted == grade["score"] else f"{grade['quality']} after hints",
        "strengths": strengths,
        "improvements": improvements,
        "missing_concepts": grade["missing"],
        "model_answer": task.model_answer,
        "next_step": (
            "Re-run using only the artifacts and no hints."
            if adjusted < 75
            else "Move to another scenario for the same role or increase seniority."
        ),
    }


def evaluate_interview_answer(
    role: dict[str, Any],
    level: str,
    dimension: str,
    question: str,
    answer: str,
) -> dict[str, Any]:
    guidance = DIMENSION_GUIDANCE.get(
        dimension,
        {
            "required": (_concept("risk"), _concept("control"), _concept("outcome")),
            "model": "State the security objective, the control or decision, the evidence, the tradeoff, and the measurable outcome.",
        },
    )

    focus_groups = tuple(_concept(term) for term in role.get("focus", ())[:3])
    required = tuple(guidance["required"]) + focus_groups[:1]
    bonus = focus_groups[1:]
    grade = _grade(answer, required, bonus)

    strengths = [f"Covered: {concept}" for concept in grade["matched"][:5]]
    improvements = [f"Make {concept} explicit." for concept in grade["missing"][:5]]
    if len(answer.split()) < 45:
        improvements.append("Add one concrete implementation detail or example; the answer is currently brief.")
    if dimension in {"Metrics", "Hands-on", "Scale"} and not re.search(r"\b\d+%|\b\d+\b", answer):
        improvements.append("Use a concrete metric, scale, or before/after measure if you have one.")
    if not improvements:
        improvements.append("No critical content gap detected; tighten structure and lead with the decision/outcome.")

    role_focus = ", ".join(role.get("focus", ())[:3])
    model_answer = (
        f"For a {role['name']} answer at {level} level: {guidance['model']} "
        f"Anchor the response in role-relevant concepts such as {role_focus}. "
        "A strong answer should make the decision, technical mechanism, evidence, tradeoff, and measurable outcome easy to follow."
    )

    return {
        "role_id": role["role_id"],
        "level": level,
        "dimension": dimension,
        "question": question,
        "score": grade["score"],
        "quality": grade["quality"],
        "strengths": strengths,
        "improvements": improvements,
        "missing_concepts": grade["missing"],
        "model_answer": model_answer,
        "rubric": {
            "content_coverage": 80,
            "depth_and_role_relevance": 20,
            "note": "Deterministic rubric evaluation; it is guidance, not a hiring decision.",
        },
    }


class CareerAttemptStore:
    """Append-only local store for interview and simulation evaluations."""

    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.path = state_dir / "career_attempts.jsonl"

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        prior = self.attempts()

        def same_attempt_group(row: dict[str, Any]) -> bool:
            if row.get("kind") != kind:
                return False
            if kind == "interview":
                return (
                    row.get("role_id") == payload.get("role_id")
                    and row.get("level") == payload.get("level")
                    and row.get("dimension") == payload.get("dimension")
                    and row.get("question") == payload.get("question")
                )
            return (
                row.get("scenario_id") == payload.get("scenario_id")
                and row.get("task_id") == payload.get("task_id")
            )

        grouped = [row for row in prior if same_attempt_group(row)]
        previous_best = max(
            (int(row.get("score", 0)) for row in grouped),
            default=0,
        )
        current_score = int(payload.get("score", 0))
        attempt_number = len(grouped) + 1

        record = {
            "attempt_id": "CA-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "attempt_number": attempt_number,
            "previous_best_score": previous_best,
            "best_score": max(previous_best, current_score),
            "score_delta_from_previous_best": current_score - previous_best,
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def attempts(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return list(reversed(rows))
