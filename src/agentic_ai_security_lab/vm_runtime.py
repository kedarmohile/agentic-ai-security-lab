"""Portable VM lab runtime backed by Multipass.

Git stores lab blueprints and cloud-init, never VM disk images. A user's host
materializes a fresh Ubuntu guest locally. The same blueprint works on Linux,
macOS, and Windows through Multipass' platform-specific virtualization backend.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, asdict
from importlib.resources import files
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VmBlueprint:
    blueprint_id: str
    title: str
    image: str
    cpus: int
    memory: str
    disk: str
    cloud_init: str
    scenario_ids: tuple[str, ...]
    description: str


def _blueprint_root() -> Any:
    return files("agentic_ai_security_lab").joinpath("vm_blueprints")


def _load_blueprints() -> dict[str, VmBlueprint]:
    result: dict[str, VmBlueprint] = {}
    root = _blueprint_root()
    for child in root.iterdir():
        if not child.is_dir():
            continue
        manifest = child.joinpath("lab.json")
        if not manifest.is_file():
            continue
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        bp = VmBlueprint(
            blueprint_id=raw["blueprint_id"],
            title=raw["title"],
            image=raw.get("image", "24.04"),
            cpus=int(raw.get("cpus", 2)),
            memory=str(raw.get("memory", "2G")),
            disk=str(raw.get("disk", "8G")),
            cloud_init=str(raw.get("cloud_init", "cloud-init.yaml")),
            scenario_ids=tuple(raw.get("scenario_ids", [])),
            description=str(raw.get("description", "")),
        )
        result[bp.blueprint_id] = bp
    return result


def vm_catalog() -> dict[str, Any]:
    blueprints = _load_blueprints()
    return {
        "provider": {
            "name": "Multipass",
            "open_source": True,
            "license": "GPL-3.0",
            "host_platforms": ["Linux", "macOS", "Windows"],
            "guest_family": "Ubuntu Linux",
            "reset_model": "destroy-and-recreate",
            "note": (
                "Git stores blueprints/cloud-init only. VM disks are created locally. "
                "Destroy/recreate is the portable reset mechanism; snapshots are optional "
                "when the selected Multipass backend supports them."
            ),
        },
        "blueprints": [asdict(bp) for bp in blueprints.values()],
    }


def blueprint_for_scenario(scenario_id: str) -> VmBlueprint | None:
    for bp in _load_blueprints().values():
        if scenario_id in bp.scenario_ids:
            return bp
    return None


def _safe_instance_name(blueprint_id: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", blueprint_id.lower()).strip("-")
    return ("aasl-" + cleaned)[:63]


class MultipassRuntime:
    """Thin, explicit wrapper around the Multipass CLI."""

    def __init__(self, binary: str | None = None) -> None:
        self.binary = binary or shutil.which("multipass") or "multipass"

    def available(self) -> bool:
        return shutil.which(self.binary) is not None or (
            Path(self.binary).is_file() if "/" in self.binary else False
        )

    def _run(
        self,
        args: list[str],
        *,
        timeout: int = 120,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        if not self.available():
            raise ValueError(
                "Multipass is not installed. Install it from https://multipass.run/ "
                "before starting VM-backed labs."
            )
        result = subprocess.run(
            [self.binary, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if check and result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise ValueError(f"multipass {' '.join(args)} failed: {detail}")
        return result

    def host_info(self) -> dict[str, Any]:
        version = None
        if self.available():
            result = self._run(["version"], timeout=20, check=False)
            version = (result.stdout or result.stderr).strip()
        return {
            "available": self.available(),
            "binary": self.binary,
            "version": version,
        }

    def list_instances(self) -> list[dict[str, Any]]:
        if not self.available():
            return []
        result = self._run(["list", "--format", "json"], timeout=30)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        return payload.get("list", []) if isinstance(payload, dict) else []

    def instance_status(self, blueprint_id: str) -> dict[str, Any]:
        bp = _load_blueprints().get(blueprint_id)
        if bp is None:
            raise ValueError(f"unknown VM blueprint: {blueprint_id}")
        name = _safe_instance_name(blueprint_id)
        instance = next(
            (row for row in self.list_instances() if row.get("name") == name),
            None,
        )
        return {
            "blueprint": asdict(bp),
            "instance_name": name,
            "instance": instance,
            "provider": self.host_info(),
        }

    def _delete_if_present(self, name: str) -> None:
        if any(row.get("name") == name for row in self.list_instances()):
            self._run(["delete", name, "--purge"], timeout=60)

    def start(self, blueprint_id: str, *, fresh: bool = False) -> dict[str, Any]:
        bp = _load_blueprints().get(blueprint_id)
        if bp is None:
            raise ValueError(f"unknown VM blueprint: {blueprint_id}")
        name = _safe_instance_name(blueprint_id)
        existing = next(
            (row for row in self.list_instances() if row.get("name") == name),
            None,
        )
        if existing and fresh:
            self._delete_if_present(name)
            existing = None

        if not existing:
            bp_dir = _blueprint_root().joinpath(bp.blueprint_id)
            cloud_init = bp_dir.joinpath(bp.cloud_init)
            if not cloud_init.is_file():
                raise ValueError(f"cloud-init missing for blueprint: {bp.blueprint_id}")
            self._run(
                [
                    "launch",
                    bp.image,
                    "--name",
                    name,
                    "--cpus",
                    str(bp.cpus),
                    "--memory",
                    bp.memory,
                    "--disk",
                    bp.disk,
                    "--cloud-init",
                    str(cloud_init),
                    "--timeout",
                    "900",
                ],
                timeout=960,
            )
        else:
            state = str(existing.get("state", "")).lower()
            if state not in {"running", "starting"}:
                self._run(["start", name], timeout=180)

        return self.instance_status(blueprint_id)

    def reset(self, blueprint_id: str) -> dict[str, Any]:
        """Portable reset: delete and materialize the guest again from Git blueprint."""
        bp = _load_blueprints().get(blueprint_id)
        if bp is None:
            raise ValueError(f"unknown VM blueprint: {blueprint_id}")
        name = _safe_instance_name(blueprint_id)
        self._delete_if_present(name)
        return self.start(blueprint_id)

    def stop(self, blueprint_id: str) -> dict[str, Any]:
        bp = _load_blueprints().get(blueprint_id)
        if bp is None:
            raise ValueError(f"unknown VM blueprint: {blueprint_id}")
        name = _safe_instance_name(blueprint_id)
        if any(row.get("name") == name for row in self.list_instances()):
            self._run(["stop", name], timeout=180)
        return self.instance_status(blueprint_id)

    def destroy(self, blueprint_id: str) -> dict[str, Any]:
        bp = _load_blueprints().get(blueprint_id)
        if bp is None:
            raise ValueError(f"unknown VM blueprint: {blueprint_id}")
        name = _safe_instance_name(blueprint_id)
        self._delete_if_present(name)
        return self.instance_status(blueprint_id)

    def exec(self, blueprint_id: str, command: list[str]) -> dict[str, Any]:
        if not command or not all(isinstance(v, str) and v for v in command):
            raise ValueError("VM command must be a non-empty list of strings")
        status = self.start(blueprint_id)
        name = status["instance_name"]
        result = self._run(["exec", name, "--", *command], timeout=120)
        return {
            "blueprint_id": blueprint_id,
            "instance_name": name,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    def shell_command(self, blueprint_id: str) -> str:
        bp = _load_blueprints().get(blueprint_id)
        if bp is None:
            raise ValueError(f"unknown VM blueprint: {blueprint_id}")
        return f"multipass shell {_safe_instance_name(blueprint_id)}"
