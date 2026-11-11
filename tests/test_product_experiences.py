import json
import sys
from pathlib import Path

from agentic_ai_security_lab.orchestration import RunStore, execute_lab
from agentic_ai_security_lab.product_experiences import (
    ATLAS_TACTICS,
    ROLE_TRACKS,
    TargetRegistry,
    academy_catalog,
    academy_progress,
    career_catalog,
    interview_session,
)


def test_academy_exposes_all_sixteen_atlas_tactics() -> None:
    data = academy_catalog()

    assert len(data["atlas_tactics"]) == 16
    assert {row["name"] for row in data["atlas_tactics"]} == {
        "Reconnaissance",
        "Resource Development",
        "AI Attack Adaptation",
        "Initial Access",
        "AI Model Access",
        "Execution",
        "Persistence",
        "Privilege Escalation",
        "Defense Evasion",
        "Credential Access",
        "Discovery",
        "Lateral Movement",
        "Collection",
        "Command and Control",
        "Exfiltration",
        "Impact",
    }
    assert any(row["status"] == "mission-linked" for row in ATLAS_TACTICS)
    assert any(row["status"] == "roadmap" for row in ATLAS_TACTICS)


def test_academy_progress_requires_secure_and_vulnerable_evidence(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.append_run(execute_lab("lab01", "secure"))

    progress = academy_progress(store)
    mission = next(row for row in progress["missions"] if row["mission_id"] == "M-001")
    assert mission["secure_done"] is True
    assert mission["vulnerable_done"] is False
    assert mission["complete"] is False

    store.append_run(execute_lab("lab01", "vulnerable"))
    progress = academy_progress(store)
    mission = next(row for row in progress["missions"] if row["mission_id"] == "M-001")
    assert mission["complete"] is True
    assert progress["xp"] >= mission["xp"]


def test_commercial_reference_patterns_are_explicitly_unaffiliated() -> None:
    refs = academy_catalog()["references"]
    names = {ref["name"] for ref in refs}

    assert "Hack The Box Enterprise" in names
    assert "Immersive" in names
    assert all("not affiliated" in ref["note"].lower() for ref in refs)


def test_career_lab_has_broad_security_role_coverage() -> None:
    data = career_catalog()
    role_ids = {role["role_id"] for role in ROLE_TRACKS}

    assert len(ROLE_TRACKS) >= 24
    assert data["framework"]["version"] == "2.2.0"
    assert data["framework"]["work_roles"] == 42
    for required in {
        "soc-analyst",
        "appsec",
        "red-team",
        "soar-security-automation",
        "threat-intel",
        "cloud-security",
        "grc-risk",
        "security-leadership",
        "ai-security",
    }:
        assert required in role_ids


def test_interview_session_covers_multiple_angles_and_seniority() -> None:
    session = interview_session("ai-security", "principal")
    dimensions = {question["dimension"] for question in session["questions"]}

    assert len(session["questions"]) >= 10
    assert "Technical depth" in dimensions
    assert "Proactive security" in dimensions
    assert "Metrics" in dimensions
    assert "Leadership" in dimensions
    assert "Scale" in dimensions


def test_local_target_analysis_discovers_security_surfaces(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    repo.mkdir()
    (repo / "agent.py").write_text(
        "memory_store = {}\n"
        "def browser_tool(): pass\n"
        "oauth_token = 'test'\n"
        "def retrieve_vector(): pass\n"
        "def handoff_agent(): pass\n",
        encoding="utf-8",
    )

    registry = TargetRegistry(tmp_path / "state")
    target = registry.register("demo-agent", "local", str(repo))
    analyzed = registry.analyze(target["target_id"])

    assert analyzed["analysis"]["status"] == "analyzed"
    compatible = set(analyzed["analysis"]["compatible_labs"])
    assert {"lab01", "lab02", "lab03", "lab04", "lab05"}.issubset(compatible)


def test_target_scaffold_does_not_run_code(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    repo.mkdir()

    registry = TargetRegistry(tmp_path / "state")
    target = registry.register("safe-target", "local", str(repo))
    registry.scaffold(target["target_id"])

    manifest = repo / ".aasl" / "target.json"
    guide = repo / "security" / "aasl" / "README.md"

    assert manifest.is_file()
    assert guide.is_file()
    assert json.loads(manifest.read_text(encoding="utf-8"))["commands"] == {}


def test_explicit_target_adapter_can_run_and_persist_result(tmp_path: Path) -> None:
    repo = tmp_path / "target"
    repo.mkdir()
    (repo / ".aasl").mkdir()
    adapter = repo / "adapter.py"
    adapter.write_text(
        "import json\n"
        "print(json.dumps({'finding': False, 'verdict': 'pass', 'severity': 'none', 'adapter': 'ok'}))\n",
        encoding="utf-8",
    )
    (repo / ".aasl" / "target.json").write_text(
        json.dumps(
            {
                "version": 1,
                "commands": {
                    "lab01": [sys.executable, "adapter.py", "--mode", "{mode}"]
                },
            }
        ),
        encoding="utf-8",
    )

    registry = TargetRegistry(tmp_path / "state")
    target = registry.register("adapter-target", "local", str(repo))
    record = registry.run(target["target_id"], "lab01", "secure")

    assert record["result"]["verdict"] == "pass"
    assert record["result"]["adapter"] == "ok"
    assert registry.target_runs()[0]["target_run_id"] == record["target_run_id"]
