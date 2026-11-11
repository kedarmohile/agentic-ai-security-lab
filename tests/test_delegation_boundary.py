from dataclasses import replace

from agentic_ai_security_lab.delegation_boundary import (
    ACTION_PUBLISH,
    DELEGATE_ID,
    DEPUTY_ID,
    PRINCIPAL_ID,
    RESOURCE_Q4,
    BrokerMode,
    DelegatedAction,
    DelegationAuthority,
    DelegationBroker,
    DeputyCapabilityPolicy,
    LabMode,
    Verdict,
    run_delegation_boundary_lab,
)


EXAMPLE_SECRET = b"lab04-example-secret"


def test_secure_mode_denies_scope_escalation_through_privileged_deputy() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.SECURE,
        secret=EXAMPLE_SECRET,
        run_id="test-secure",
    )

    assert result.control_delegation_succeeded is True, "exact delegated control must prove the chain works"
    assert result.deputy_has_local_capability is True, "deputy must actually hold the broader local capability"
    assert result.delegation_valid_for_request is False, "read delegation must not authorize publish"
    assert result.delegated_action_executed is False
    assert result.finding is False
    assert result.verdict == Verdict.PASS.value


def test_vulnerable_mode_exposes_confused_deputy_failure() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.VULNERABLE,
        secret=EXAMPLE_SECRET,
        run_id="test-vulnerable",
    )

    assert result.deputy_has_local_capability is True
    assert result.delegation_valid_for_request is False, "original principal did not delegate publish"
    assert result.delegated_action_executed is True, "vulnerable broker trusts deputy privilege alone"
    assert result.authorization_source == "deputy-local-privilege"
    assert result.finding is True
    assert result.verdict == Verdict.FAIL.value
    assert result.severity == "high"


def test_exact_delegation_allows_action_without_finding() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.EXACT_DELEGATED,
        secret=EXAMPLE_SECRET,
        run_id="test-exact",
    )

    assert result.delegation_valid_for_request is True
    assert result.delegated_action_executed is True
    assert result.authorization_source == "delegation-grant"
    assert result.finding is False
    assert result.verdict == Verdict.EXPECTED_AUTHORIZED.value


def test_resource_substitution_is_denied() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.RESOURCE_SUBSTITUTION,
        secret=EXAMPLE_SECRET,
        run_id="test-resource",
    )

    assert result.delegation_token_supplied is True
    assert result.delegation_valid_for_request is False, "Q4 delegation must not authorize executive resource"
    assert result.deputy_has_local_capability is True, "deputy privilege must exist so delegation is the deciding boundary"
    assert result.delegated_action_executed is False
    assert result.verdict == Verdict.PASS.value


def test_delegate_substitution_is_denied() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.DELEGATE_SUBSTITUTION,
        secret=EXAMPLE_SECRET,
        run_id="test-delegate",
    )

    assert result.delegate_id != DELEGATE_ID, "scenario must substitute the delegate"
    assert result.delegation_valid_for_request is False
    assert result.delegated_action_executed is False
    assert result.verdict == Verdict.PASS.value


def test_request_replay_is_denied() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.REQUEST_REPLAY,
        secret=EXAMPLE_SECRET,
        run_id="test-replay",
    )

    assert result.delegation_token_supplied is True
    assert result.delegation_valid_for_request is False, "prior request grant must not replay"
    assert result.delegated_action_executed is False


def test_delegation_token_binds_every_chain_dimension() -> None:
    authority = DelegationAuthority(EXAMPLE_SECRET)
    original = DelegatedAction(
        principal_id=PRINCIPAL_ID,
        delegate_id=DELEGATE_ID,
        deputy_id=DEPUTY_ID,
        request_id="request-001",
        action=ACTION_PUBLISH,
        resource=RESOURCE_Q4,
    )
    token = authority.issue(original)

    mutations = [
        replace(original, principal_id="principal-bob"),
        replace(original, delegate_id="agent-c"),
        replace(original, deputy_id="agent-d"),
        replace(original, request_id="request-002"),
        replace(original, action="read"),
        replace(original, resource="report/executive"),
    ]

    assert authority.verify(original, token) is True
    for changed in mutations:
        assert authority.verify(changed, token) is False, "delegation must bind every chain dimension"


def test_deputy_local_capability_is_required_even_with_valid_delegation() -> None:
    authority = DelegationAuthority(EXAMPLE_SECRET)
    request = DelegatedAction(
        principal_id=PRINCIPAL_ID,
        delegate_id=DELEGATE_ID,
        deputy_id=DEPUTY_ID,
        request_id="request-001",
        action=ACTION_PUBLISH,
        resource=RESOURCE_Q4,
    )
    token = authority.issue(request)
    deputy_policy = DeputyCapabilityPolicy(
        deputy_id=DEPUTY_ID,
        capabilities=frozenset(),
    )
    broker = DelegationBroker(
        authority,
        deputy_policy,
        mode=BrokerMode.SECURE,
    )

    decision = broker.authorize(request, token)

    assert decision.allowed is False
    assert decision.reason == "deputy-lacks-local-capability"


def test_secure_broker_does_not_confuse_deputy_privilege_with_delegation() -> None:
    authority = DelegationAuthority(EXAMPLE_SECRET)
    request = DelegatedAction(
        principal_id=PRINCIPAL_ID,
        delegate_id=DELEGATE_ID,
        deputy_id=DEPUTY_ID,
        request_id="request-001",
        action=ACTION_PUBLISH,
        resource=RESOURCE_Q4,
    )
    read_only_grant = replace(request, action="read")
    token = authority.issue(read_only_grant)
    deputy_policy = DeputyCapabilityPolicy(
        deputy_id=DEPUTY_ID,
        capabilities=frozenset({(ACTION_PUBLISH, RESOURCE_Q4)}),
    )
    broker = DelegationBroker(
        authority,
        deputy_policy,
        mode=BrokerMode.SECURE,
    )

    decision = broker.authorize(request, token)

    assert deputy_policy.can(DEPUTY_ID, ACTION_PUBLISH, RESOURCE_Q4) is True
    assert decision.allowed is False
    assert decision.reason == "delegation-does-not-authorize-request"


def test_result_evidence_omits_raw_delegation_token_and_secret() -> None:
    result = run_delegation_boundary_lab(
        mode=LabMode.EXACT_DELEGATED,
        secret=EXAMPLE_SECRET,
        run_id="test-evidence",
    )
    authority = DelegationAuthority(EXAMPLE_SECRET)
    request = DelegatedAction(
        principal_id=PRINCIPAL_ID,
        delegate_id=DELEGATE_ID,
        deputy_id=DEPUTY_ID,
        request_id="request-001",
        action=ACTION_PUBLISH,
        resource=RESOURCE_Q4,
    )
    raw_token = authority.issue(request)

    serialized = str(result.to_dict())
    assert raw_token not in serialized, "result should contain only the grant fingerprint"
    assert "lab04-example-secret" not in serialized
    assert len(result.request_sha256) == 64
    assert result.delegation_token_sha256 is not None
    assert len(result.delegation_token_sha256) == 64
