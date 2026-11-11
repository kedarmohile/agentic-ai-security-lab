from agentic_ai_security_lab.memory_isolation import (
    InMemoryPreferenceMemory,
    IsolationPolicy,
    MemoryContext,
    NamespaceMode,
    Verdict,
    run_memory_isolation_lab,
)


FIXED_CANARY = "CANARY-ORCHID-7F3A"
FIXED_RUN_ID = "test-run-001"


def test_actor_scoped_memory_preserves_actor_a_and_blocks_actor_b() -> None:
    backend = InMemoryPreferenceMemory(NamespaceMode.ACTOR_SCOPED)

    result = run_memory_isolation_lab(
        backend,
        canary=FIXED_CANARY,
        run_id=FIXED_RUN_ID,
    )

    assert result.actor_a_control_recall is True, "positive control must prove persistence works"
    assert result.actor_b_observed_canary is False, "Actor B must not see Actor A memory"
    assert result.finding is False, "isolated memory must not produce a finding"
    assert result.verdict == Verdict.PASS.value


def test_shared_namespace_is_flagged_when_isolation_is_expected() -> None:
    backend = InMemoryPreferenceMemory(NamespaceMode.SHARED)

    result = run_memory_isolation_lab(
        backend,
        canary=FIXED_CANARY,
        run_id=FIXED_RUN_ID,
    )

    assert result.actor_a_control_recall is True, "positive control must prove persistence works"
    assert result.actor_b_observed_canary is True, "shared namespace should expose the canary"
    assert result.finding is True, "cross-actor canary exposure is a finding when isolation is expected"
    assert result.verdict == Verdict.FAIL.value
    assert result.severity == "high"


def test_shared_namespace_is_not_a_finding_when_policy_allows_sharing() -> None:
    backend = InMemoryPreferenceMemory(NamespaceMode.SHARED)

    result = run_memory_isolation_lab(
        backend,
        policy=IsolationPolicy(expected_isolation=False),
        canary=FIXED_CANARY,
        run_id=FIXED_RUN_ID,
    )

    assert result.actor_b_observed_canary is True, "control should demonstrate the shared namespace"
    assert result.finding is False, "deliberately shared memory must not be mislabeled as a vulnerability"
    assert result.verdict == Verdict.EXPECTED_SHARED.value


class NonPersistentMemory:
    def remember(self, context: MemoryContext, key: str, value: str) -> None:
        return None

    def recall(self, context: MemoryContext, key: str) -> str | None:
        return None


def test_failed_positive_control_makes_result_inconclusive() -> None:
    result = run_memory_isolation_lab(
        NonPersistentMemory(),
        canary=FIXED_CANARY,
        run_id=FIXED_RUN_ID,
    )

    assert result.actor_a_control_recall is False, "test fixture intentionally does not persist"
    assert result.finding is False, "a broken persistence control cannot support a security finding"
    assert result.verdict == Verdict.INCONCLUSIVE.value


def test_result_does_not_expose_raw_canary() -> None:
    backend = InMemoryPreferenceMemory(NamespaceMode.SHARED)

    result = run_memory_isolation_lab(
        backend,
        canary=FIXED_CANARY,
        run_id=FIXED_RUN_ID,
    )

    serialized = str(result.to_dict())
    assert FIXED_CANARY not in serialized, "result artifacts should contain only the canary fingerprint"
    assert len(result.canary_sha256) == 64
