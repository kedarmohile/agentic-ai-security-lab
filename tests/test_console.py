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
        assert "Command Center" in html
        assert "Hunts" in html
        assert "Attack Graph" in html
        assert "https://" not in html
        assert "/api/run" in js
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
