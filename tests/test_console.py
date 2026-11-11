import json
import threading
import urllib.request
from pathlib import Path

from agentic_ai_security_lab.console_server import create_server
from agentic_ai_security_lab.orchestration import HUNTS, LABS, RunStore, catalog, execute_lab, status


def test_console_catalog_covers_all_five_labs_and_hunts() -> None:
    data = catalog()
    assert len(data["labs"]) == 5
    assert len(data["hunts"]) == 5
    assert set(LABS) == {"lab01", "lab02", "lab03", "lab04", "lab05"}
    assert {hunt.lab_id for hunt in HUNTS} == set(LABS)


def test_vulnerable_run_generates_scores_timeline_and_finding() -> None:
    record = execute_lab("lab02", "vulnerable")
    assert record["result"]["finding"] is True
    assert record["finding"] is not None
    assert record["scores"]["control"] < 50
    assert record["scores"]["exposure"] > 80
    assert record["scores"]["evidence"] >= 90
    assert len(record["timeline"]) >= 4
    assert record["points"]["earned"] == record["points"]["possible"]


def test_secure_run_is_not_converted_into_finding() -> None:
    record = execute_lab("lab01", "secure")
    assert record["result"]["finding"] is False
    assert record["finding"] is None
    assert record["scores"]["control"] >= 90
    assert record["scores"]["exposure"] < 30


def test_store_and_status_use_latest_run_per_lab(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.append_run(execute_lab("lab01", "vulnerable"))
    store.append_run(execute_lab("lab01", "secure"))
    store.append_run(execute_lab("lab05", "vulnerable"))
    summary = status(store)
    assert summary["assessed_labs"] == 2
    assert summary["total_runs"] == 3
    assert summary["findings"] == 2
    assert summary["posture_score"] is not None


def test_case_creation_persists_locally(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    case = store.create_case("Investigate credential bleed", "AASL-05-ABC123")
    assert case["status"] == "open"
    assert store.cases()[0]["finding_id"] == "AASL-05-ABC123"


def test_console_http_api_runs_lab_and_returns_status(tmp_path: Path) -> None:
    server = create_server("127.0.0.1", 0, tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(f"{base}/api/catalog") as response:
            catalog_payload = json.loads(response.read().decode("utf-8"))
        assert len(catalog_payload["labs"]) == 5

        request = urllib.request.Request(
            f"{base}/api/run",
            data=json.dumps({"lab_id": "lab03", "mode": "vulnerable"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            run = json.loads(response.read().decode("utf-8"))
        assert run["result"]["finding"] is True

        with urllib.request.urlopen(f"{base}/api/status") as response:
            summary = json.loads(response.read().decode("utf-8"))
        assert summary["total_runs"] == 1
        assert summary["high_findings"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_console_assets_are_served_without_external_cdn(tmp_path: Path) -> None:
    server = create_server("127.0.0.1", 0, tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base + "/") as response:
            html = response.read().decode("utf-8")
        with urllib.request.urlopen(base + "/app.js") as response:
            js = response.read().decode("utf-8")
        assert "AASL Security Console" in html
        assert "Start Here" in html
        assert "Academy" in html
        assert "Career Lab" in html
        assert "Interview Studio" in html
        assert "Simulation Range" in html
        assert "Target Lab" in html
        assert "SECURITY FRAMEWORK STACK" in html
        assert "COMMERCIAL REFERENCE" in html
        assert "MITRE ATLAS COVERAGE MAP" in html
        assert "WHAT THIS PLATFORM DOES" in html
        assert "TEST YOUR OWN APPLICATION" in html
        assert "Command Center" in html
        assert "Hunts" in html
        assert "Attack Graph" in html
        assert "https://" not in html
        assert "/api/run" in js
        assert "/api/career/evaluate-interview" in js
        assert "/api/career/evaluate-simulation" in js
        assert "/api/vm/start" in js
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_console_readability_overrides_are_present() -> None:
    from importlib.resources import files

    css = files("agentic_ai_security_lab").joinpath("console_assets", "styles.css").read_text(encoding="utf-8")

    assert "html { font-size: 16px; }" in css
    assert "body { font-size: 17px;" in css
    assert ".hunt-title { font-size: 14px;" in css
    assert ".json-block { font-size: 12px;" in css


def test_target_integration_guide_and_example_ship_with_package_repo() -> None:
    from pathlib import Path

    assert Path("docs/test-your-app.md").is_file()
    assert Path("examples/targets/lab01_memory_adapter.py").is_file()


def test_v2_product_apis(tmp_path: Path) -> None:
    server = create_server("127.0.0.1", 0, tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    try:
        with urllib.request.urlopen(f"{base}/api/academy") as response:
            academy = json.loads(response.read().decode("utf-8"))
        assert len(academy["atlas_tactics"]) == 16

        with urllib.request.urlopen(f"{base}/api/career") as response:
            career = json.loads(response.read().decode("utf-8"))
        assert len(career["roles"]) >= 24
        assert len(career["frameworks"]["owasp_web_2025"]["items"]) == 10
        assert len(career["frameworks"]["owasp_llm_2026"]["items"]) == 10
        assert len(career["frameworks"]["owasp_agentic_2026"]["items"]) == 10

        with urllib.request.urlopen(f"{base}/api/vm/catalog") as response:
            vm_data = json.loads(response.read().decode("utf-8"))
        assert len(vm_data["blueprints"]) >= 3
        assert "available" in vm_data["host"]

        interview_request = urllib.request.Request(
            f"{base}/api/interview",
            data=json.dumps({"role_id": "soc-analyst", "level": "senior"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(interview_request) as response:
            session = json.loads(response.read().decode("utf-8"))
        assert session["role"]["name"] == "SOC Analyst"
        assert len(session["questions"]) >= 8


        simulation_request = urllib.request.Request(
            f"{base}/api/career/simulations",
            data=json.dumps({"role_id": "ai-security"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(simulation_request) as response:
            simulations = json.loads(response.read().decode("utf-8"))
        assert any(
            row["scenario_id"] == "sim-ai-agent-boundary"
            for row in simulations["scenarios"]
        )

        eval_interview_request = urllib.request.Request(
            f"{base}/api/career/evaluate-interview",
            data=json.dumps(
                {
                    "role_id": "soc-analyst",
                    "level": "senior",
                    "dimension": "Adversarial scenario",
                    "question": "How would you triage this incident?",
                    "answer": (
                        "I would triage confidence and scope, preserve evidence, "
                        "contain the affected session, and make a risk decision."
                    ),
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(eval_interview_request) as response:
            interview_eval = json.loads(response.read().decode("utf-8"))
        assert "score" in interview_eval
        assert "model_answer" in interview_eval
        assert "improvements" in interview_eval

        eval_sim_request = urllib.request.Request(
            f"{base}/api/career/evaluate-simulation",
            data=json.dumps(
                {
                    "scenario_id": "sim-auth-bypass-toy",
                    "task_id": "bypass-analysis",
                    "answer": (
                        "X-Demo-Role is a caller-controlled header. Supplying admin "
                        "bypasses authorization. Use trusted server-side session claims "
                        "and an authorization policy instead."
                    ),
                    "hints_used": 0,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(eval_sim_request) as response:
            sim_eval = json.loads(response.read().decode("utf-8"))
        assert "score" in sim_eval
        assert "model_answer" in sim_eval

        target_root = tmp_path / "repo"
        target_root.mkdir()
        (target_root / "agent.py").write_text("def browser_tool(): pass\n", encoding="utf-8")
        register_request = urllib.request.Request(
            f"{base}/api/targets",
            data=json.dumps(
                {
                    "name": "local-demo",
                    "source_type": "local",
                    "location": str(target_root),
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(register_request) as response:
            target = json.loads(response.read().decode("utf-8"))

        analyze_request = urllib.request.Request(
            f"{base}/api/targets/analyze",
            data=json.dumps({"target_id": target["target_id"]}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(analyze_request) as response:
            analyzed = json.loads(response.read().decode("utf-8"))
        assert analyzed["analysis"]["status"] == "analyzed"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_v2_repository_docs_are_aligned_with_product() -> None:
    from pathlib import Path

    readme = Path("README.md").read_text(encoding="utf-8")
    architecture = Path("docs/security-console.md").read_text(encoding="utf-8")
    target_guide = Path("docs/test-your-app.md").read_text(encoding="utf-8")
    scoring = Path("docs/console-scoring.md").read_text(encoding="utf-8")
    career = Path("docs/career-lab.md").read_text(encoding="utf-8")
    frameworks = Path("docs/security-frameworks.md").read_text(encoding="utf-8")
    vm_labs = Path("docs/vm-labs.md").read_text(encoding="utf-8")

    assert "Academy" in readme
    assert "Career Lab" in readme
    assert "Target Lab" in readme
    assert "127.0.0.1:8877" in readme

    assert "/api/academy" in architecture
    assert "/api/career" in architecture
    assert "/api/targets" in architecture
    assert "127.0.0.1:8877" in architecture

    assert "future extension" not in target_guide
    assert "Clone & Analyze" in target_guide
    assert ".aasl/target.json" in target_guide

    assert "Academy XP and ranks" in scoring
    assert "Target Lab results" in scoring

    assert "Interview Studio" in career
    assert "Simulation Range" in career
    assert "OWASP Top 10:2025" in career
    assert "MITRE ATLAS" in career

    assert "OWASP Top 10:2025" in frameworks
    assert "OWASP Top 10 for LLM Applications 2026" in frameworks
    assert "OWASP Top 10 for Agentic Applications 2026" in frameworks
    assert "MITRE ATLAS" in frameworks

    assert "Multipass" in vm_labs
    assert "destroy and recreate" in vm_labs

    for path in (
        "docs/academy.md",
        "docs/career-lab.md",
        "docs/security-frameworks.md",
        "docs/vm-labs.md",
        "docs/target-lab.md",
        "docs/product-reference-models.md",
        "docs/target-manifest.md",
    ):
        assert Path(path).is_file()
