"""Local HTTP server for the Agentic AI Security Console."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .orchestration import RunStore, catalog, execute_lab, status
from .product_experiences import ROLE_TRACKS, TargetRegistry, academy_catalog, academy_progress, career_catalog, interview_session
from .career_simulations import CareerAttemptStore, career_simulation_catalog, evaluate_interview_answer, evaluate_simulation_task
from .vm_runtime import MultipassRuntime, blueprint_for_scenario, vm_catalog


def _asset_root() -> Any:
    return files("agentic_ai_security_lab").joinpath("console_assets")


class ConsoleHandler(BaseHTTPRequestHandler):
    server_version = "AASLConsole/0.8"

    @property
    def store(self) -> RunStore:
        return self.server.store  # type: ignore[attr-defined]

    @property
    def targets(self) -> TargetRegistry:
        return TargetRegistry(self.store.state_dir)

    @property
    def career_attempts(self) -> CareerAttemptStore:
        return CareerAttemptStore(self.store.state_dir)

    @property
    def vm_runtime(self) -> MultipassRuntime:
        return MultipassRuntime()

    def _json(self, payload: Any, status_code: int = HTTPStatus.OK) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _serve_asset(self, path: str) -> None:
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        if ".." in Path(relative).parts:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        asset = _asset_root().joinpath(relative)
        if not asset.is_file():
            asset = _asset_root().joinpath("index.html")
        data = asset.read_bytes()
        content_type, _ = mimetypes.guess_type(asset.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/catalog":
            self._json(catalog())
            return
        if path == "/api/academy":
            self._json(academy_catalog())
            return
        if path == "/api/academy/progress":
            self._json(academy_progress(self.store))
            return
        if path == "/api/career":
            self._json(career_catalog())
            return
        if path == "/api/career/attempts":
            self._json({"attempts": self.career_attempts.attempts()})
            return
        if path == "/api/vm/catalog":
            payload = vm_catalog()
            payload["host"] = self.vm_runtime.host_info()
            self._json(payload)
            return
        if path == "/api/targets":
            self._json({"targets": self.targets.targets(), "runs": self.targets.target_runs()})
            return
        if path == "/api/status":
            self._json(status(self.store))
            return
        if path == "/api/runs":
            self._json({"runs": self.store.runs()})
            return
        if path == "/api/findings":
            self._json({"findings": self.store.findings()})
            return
        if path == "/api/cases":
            self._json({"cases": self.store.cases()})
            return
        self._serve_asset(path)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/run":
                record = execute_lab(str(payload.get("lab_id")), str(payload.get("mode")))
                self.store.append_run(record)
                self._json(record, HTTPStatus.CREATED)
                return
            if path == "/api/interview":
                session = interview_session(str(payload.get("role_id")), str(payload.get("level", "senior")))
                self._json(session, HTTPStatus.CREATED)
                return
            if path == "/api/career/simulations":
                data = career_simulation_catalog(str(payload.get("role_id", "")) or None)
                self._json(data, HTTPStatus.CREATED)
                return
            if path == "/api/career/evaluate-interview":
                role_id = str(payload.get("role_id", ""))
                role = next((r for r in ROLE_TRACKS if r["role_id"] == role_id), None)
                if role is None:
                    raise ValueError(f"unknown role: {role_id}")
                result = evaluate_interview_answer(
                    role,
                    str(payload.get("level", "senior")),
                    str(payload.get("dimension", "")),
                    str(payload.get("question", "")),
                    str(payload.get("answer", "")),
                )
                record = self.career_attempts.append("interview", result)
                self._json(record, HTTPStatus.CREATED)
                return
            if path == "/api/career/evaluate-simulation":
                result = evaluate_simulation_task(
                    str(payload.get("scenario_id", "")),
                    str(payload.get("task_id", "")),
                    str(payload.get("answer", "")),
                    int(payload.get("hints_used", 0)),
                )
                record = self.career_attempts.append("simulation", result)
                self._json(record, HTTPStatus.CREATED)
                return
            if path == "/api/vm/status":
                blueprint_id = str(payload.get("blueprint_id", ""))
                result = self.vm_runtime.instance_status(blueprint_id)
                result["shell_command"] = self.vm_runtime.shell_command(blueprint_id)
                self._json(result, HTTPStatus.CREATED)
                return
            if path == "/api/vm/start":
                blueprint_id = str(payload.get("blueprint_id", ""))
                result = self.vm_runtime.start(blueprint_id, fresh=bool(payload.get("fresh", False)))
                result["shell_command"] = self.vm_runtime.shell_command(blueprint_id)
                self._json(result, HTTPStatus.CREATED)
                return
            if path == "/api/vm/reset":
                blueprint_id = str(payload.get("blueprint_id", ""))
                result = self.vm_runtime.reset(blueprint_id)
                result["shell_command"] = self.vm_runtime.shell_command(blueprint_id)
                self._json(result, HTTPStatus.CREATED)
                return
            if path == "/api/vm/stop":
                blueprint_id = str(payload.get("blueprint_id", ""))
                result = self.vm_runtime.stop(blueprint_id)
                result["shell_command"] = self.vm_runtime.shell_command(blueprint_id)
                self._json(result, HTTPStatus.CREATED)
                return
            if path == "/api/vm/destroy":
                blueprint_id = str(payload.get("blueprint_id", ""))
                result = self.vm_runtime.destroy(blueprint_id)
                result["shell_command"] = self.vm_runtime.shell_command(blueprint_id)
                self._json(result, HTTPStatus.CREATED)
                return
            if path == "/api/targets":
                target = self.targets.register(str(payload.get("name", "")), str(payload.get("source_type", "")), str(payload.get("location", "")))
                self._json(target, HTTPStatus.CREATED)
                return
            if path == "/api/targets/analyze":
                target = self.targets.analyze(str(payload.get("target_id", "")))
                self._json(target, HTTPStatus.CREATED)
                return
            if path == "/api/targets/clone":
                target = self.targets.clone_github(str(payload.get("target_id", "")))
                self._json(target, HTTPStatus.CREATED)
                return
            if path == "/api/targets/scaffold":
                target = self.targets.scaffold(str(payload.get("target_id", "")))
                self._json(target, HTTPStatus.CREATED)
                return
            if path == "/api/targets/run":
                result = self.targets.run(str(payload.get("target_id", "")), str(payload.get("lab_id", "")), str(payload.get("mode", "secure")))
                self._json(result, HTTPStatus.CREATED)
                return
            if path == "/api/cases":
                title = str(payload.get("title", "")).strip()
                if not title:
                    raise ValueError("case title is required")
                case = self.store.create_case(title, payload.get("finding_id"))
                self._json(case, HTTPStatus.CREATED)
                return
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        if os.environ.get("AASL_CONSOLE_ACCESS_LOG") == "1":
            super().log_message(format, *args)


class ConsoleServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], state_dir: Path):
        super().__init__(address, ConsoleHandler)
        self.store = RunStore(state_dir)


def create_server(host: str = "127.0.0.1", port: int = 8877, state_dir: Path | None = None) -> ConsoleServer:
    resolved_state = state_dir or Path(os.environ.get("AASL_STATE_DIR", ".agentic-ai-security-lab"))
    return ConsoleServer((host, port), resolved_state)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Agentic AI Security Console.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        required = ("index.html", "styles.css", "app.js", "shield.svg")
        missing = [name for name in required if not _asset_root().joinpath(name).is_file()]
        if missing:
            raise SystemExit("missing console assets: " + ", ".join(missing))
        data = catalog()
        academy = academy_catalog()
        career = career_catalog()
        vms = vm_catalog()
        if len(data["labs"]) != 5 or len(data["hunts"]) != 5:
            raise SystemExit("console catalog is incomplete")
        if len(academy["atlas_tactics"]) != 16:
            raise SystemExit("MITRE ATLAS tactic map is incomplete")
        if len(career["roles"]) < 24:
            raise SystemExit("Career Lab role catalog is incomplete")
        frameworks = career.get("frameworks", {})
        if len(frameworks.get("owasp_web_2025", {}).get("items", [])) != 10:
            raise SystemExit("OWASP Web framework catalog is incomplete")
        if len(frameworks.get("owasp_llm_2026", {}).get("items", [])) != 10:
            raise SystemExit("OWASP LLM framework catalog is incomplete")
        if len(frameworks.get("owasp_agentic_2026", {}).get("items", [])) != 10:
            raise SystemExit("OWASP Agentic framework catalog is incomplete")
        if len(vms["blueprints"]) < 3:
            raise SystemExit("Career Lab VM blueprint catalog is incomplete")
        print("security console assets and catalog: ok")
        return 0

    server = create_server(args.host, args.port, args.state_dir)
    print(f"Agentic AI Security Console: http://{args.host}:{server.server_port}")
    print(f"State directory: {server.store.state_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
