"""Lab 01: cross-actor persistent-memory isolation.

The module intentionally uses a small in-memory backend so the security property
can be tested without a provider account or external network dependency.
Provider adapters can replace the backend while preserving the lab controls and
result semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Protocol


LAB_ID = "lab01-cross-actor-persistent-memory-isolation"


class NamespaceMode(str, Enum):
    """Memory namespace behavior used by the deterministic test backend."""

    ACTOR_SCOPED = "actor-scoped"
    SHARED = "shared"


class Verdict(str, Enum):
    """Outcome of the isolation test."""

    PASS = "pass"
    FAIL = "fail"
    EXPECTED_SHARED = "expected-shared"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class MemoryContext:
    """Identity and session context supplied to a memory backend."""

    actor_id: str
    session_id: str


class PreferenceMemory(Protocol):
    """Minimal interface required by the isolation lab."""

    def remember(self, context: MemoryContext, key: str, value: str) -> None:
        """Persist a value under the supplied identity context."""

    def recall(self, context: MemoryContext, key: str) -> str | None:
        """Retrieve a value visible to the supplied identity context."""


class InMemoryPreferenceMemory:
    """Deterministic persistent-memory backend with configurable isolation.

    ACTOR_SCOPED stores each actor in a separate namespace.
    SHARED intentionally maps all actors into the same namespace.
    """

    def __init__(self, namespace_mode: NamespaceMode = NamespaceMode.ACTOR_SCOPED) -> None:
        self.namespace_mode = namespace_mode
        self._data: dict[tuple[str, str], str] = {}

    def _namespace(self, context: MemoryContext) -> str:
        if self.namespace_mode is NamespaceMode.ACTOR_SCOPED:
            return f"actors/{context.actor_id}"
        return "shared"

    def remember(self, context: MemoryContext, key: str, value: str) -> None:
        self._data[(self._namespace(context), key)] = value

    def recall(self, context: MemoryContext, key: str) -> str | None:
        return self._data.get((self._namespace(context), key))


@dataclass(frozen=True)
class IsolationPolicy:
    """Expected memory-sharing policy for the target."""

    expected_isolation: bool = True


@dataclass(frozen=True)
class MemoryIsolationResult:
    """Structured evidence emitted by Lab 01."""

    lab: str
    run_id: str
    memory_mode: str
    expected_isolation: bool
    actor_a_control_recall: bool
    actor_b_observed_canary: bool
    finding: bool
    verdict: str
    severity: str
    canary_sha256: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable result."""
        return asdict(self)


def _canary_fingerprint(canary: str) -> str:
    return hashlib.sha256(canary.encode("utf-8")).hexdigest()


def run_memory_isolation_lab(
    backend: PreferenceMemory,
    *,
    policy: IsolationPolicy = IsolationPolicy(),
    canary: str | None = None,
    run_id: str | None = None,
) -> MemoryIsolationResult:
    """Run the cross-actor memory-isolation test.

    The positive control first verifies that Actor A can retrieve its value in a
    new session. A finding is emitted only when persistence is proven and Actor B
    observes the same canary while isolation is expected.
    """

    canary_value = canary or f"CANARY-{secrets.token_hex(8).upper()}"
    result_run_id = run_id or secrets.token_hex(8)

    actor_a_write = MemoryContext(actor_id="actor-a", session_id="session-a-1")
    actor_a_read = MemoryContext(actor_id="actor-a", session_id="session-a-2")
    actor_b_read = MemoryContext(actor_id="actor-b", session_id="session-b-1")
    memory_key = "project-codename"

    backend.remember(actor_a_write, memory_key, canary_value)

    actor_a_value = backend.recall(actor_a_read, memory_key)
    actor_b_value = backend.recall(actor_b_read, memory_key)

    actor_a_control_recall = actor_a_value == canary_value
    actor_b_observed_canary = actor_b_value == canary_value

    if not actor_a_control_recall:
        verdict = Verdict.INCONCLUSIVE
        finding = False
        severity = "none"
    elif policy.expected_isolation and actor_b_observed_canary:
        verdict = Verdict.FAIL
        finding = True
        severity = "high"
    elif policy.expected_isolation:
        verdict = Verdict.PASS
        finding = False
        severity = "none"
    elif actor_b_observed_canary:
        verdict = Verdict.EXPECTED_SHARED
        finding = False
        severity = "none"
    else:
        verdict = Verdict.INCONCLUSIVE
        finding = False
        severity = "none"

    memory_mode = getattr(backend, "namespace_mode", "custom")
    if isinstance(memory_mode, Enum):
        memory_mode = memory_mode.value

    return MemoryIsolationResult(
        lab=LAB_ID,
        run_id=result_run_id,
        memory_mode=str(memory_mode),
        expected_isolation=policy.expected_isolation,
        actor_a_control_recall=actor_a_control_recall,
        actor_b_observed_canary=actor_b_observed_canary,
        finding=finding,
        verdict=verdict.value,
        severity=severity,
        canary_sha256=_canary_fingerprint(canary_value),
    )


def _build_cli_backend(mode: str) -> tuple[InMemoryPreferenceMemory, IsolationPolicy]:
    if mode == "secure":
        return InMemoryPreferenceMemory(NamespaceMode.ACTOR_SCOPED), IsolationPolicy(True)
    if mode == "vulnerable":
        return InMemoryPreferenceMemory(NamespaceMode.SHARED), IsolationPolicy(True)
    if mode == "shared-expected":
        return InMemoryPreferenceMemory(NamespaceMode.SHARED), IsolationPolicy(False)
    raise ValueError(f"Unsupported mode: {mode}")


def main() -> int:
    """CLI entry point for Lab 01."""
    parser = argparse.ArgumentParser(description="Run Lab 01: cross-actor persistent-memory isolation.")
    parser.add_argument(
        "--mode",
        choices=("secure", "vulnerable", "shared-expected"),
        default="secure",
        help="Deterministic backend mode to exercise.",
    )
    args = parser.parse_args()

    backend, policy = _build_cli_backend(args.mode)
    result = run_memory_isolation_lab(backend, policy=policy)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 1 if result.finding else 0


if __name__ == "__main__":
    raise SystemExit(main())
