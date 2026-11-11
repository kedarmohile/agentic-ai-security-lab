from agentic_ai_security_lab.credential_scope import (
    ACTION,
    CHILD_AGENT,
    PARENT_AGENT,
    PUBLISH_SERVICE,
    REQUEST_ID,
    RESOURCE_Q4,
    STORAGE_SERVICE,
    CredentialClaims,
    CredentialIssuer,
    CredentialVerifier,
    LabMode,
    ServiceRequest,
    VerifierMode,
    Verdict,
    run_credential_scope_lab,
)


EXAMPLE_SECRET = b"lab05-example-secret"


def test_secure_mode_does_not_propagate_parent_credential() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.SECURE,
        secret=EXAMPLE_SECRET,
        run_id="test-secure",
    )

    assert result.owner_control_succeeded is True
    assert result.parent_credential_exposed_to_child is False
    assert result.child_received_credential is False
    assert result.child_action_executed is False
    assert result.finding is False
    assert result.verdict == Verdict.PASS.value


def test_leaked_parent_credential_is_exposure_even_when_subject_binding_blocks_use() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.LEAKED_BOUND,
        secret=EXAMPLE_SECRET,
        run_id="test-leaked-bound",
    )

    assert result.parent_credential_exposed_to_child is True
    assert result.child_credential_is_parent_token is True
    assert result.credential_exactly_valid_for_child_request is False
    assert result.child_action_executed is False
    assert result.exposure_finding is True
    assert result.unauthorized_use_finding is False
    assert result.finding is True
    assert result.verdict == Verdict.FAIL.value
    assert result.severity == "medium"


def test_vulnerable_bearer_verifier_turns_leak_into_unauthorized_use() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.VULNERABLE,
        secret=EXAMPLE_SECRET,
        run_id="test-vulnerable",
    )

    assert result.parent_credential_exposed_to_child is True
    assert result.credential_exactly_valid_for_child_request is False
    assert result.child_action_executed is True
    assert result.decision_reason == "bearer-scope-accepted"
    assert result.exposure_finding is True
    assert result.unauthorized_use_finding is True
    assert result.severity == "high"


def test_derived_child_credential_is_distinct_and_exactly_scoped() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.DERIVED_CHILD,
        secret=EXAMPLE_SECRET,
        run_id="test-derived",
    )

    assert result.parent_credential_exposed_to_child is False
    assert result.child_received_credential is True
    assert result.child_credential_is_parent_token is False
    assert result.credential_exactly_valid_for_child_request is True
    assert result.child_action_executed is True
    assert result.finding is False
    assert result.verdict == Verdict.EXPECTED_AUTHORIZED.value


def test_audience_substitution_is_denied() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.AUDIENCE_SUBSTITUTION,
        secret=EXAMPLE_SECRET,
        run_id="test-audience",
    )

    assert result.parent_credential_exposed_to_child is False
    assert result.child_received_credential is True
    assert result.credential_exactly_valid_for_child_request is False
    assert result.child_action_executed is False
    assert result.decision_reason == "credential-scope-mismatch"


def test_resource_substitution_is_denied() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.RESOURCE_SUBSTITUTION,
        secret=EXAMPLE_SECRET,
        run_id="test-resource",
    )

    assert result.credential_exactly_valid_for_child_request is False
    assert result.child_action_executed is False
    assert result.verdict == Verdict.PASS.value


def test_request_replay_is_denied() -> None:
    result = run_credential_scope_lab(
        mode=LabMode.REQUEST_REPLAY,
        secret=EXAMPLE_SECRET,
        run_id="test-replay",
    )

    assert result.credential_exactly_valid_for_child_request is False
    assert result.child_action_executed is False
    assert result.decision_reason == "credential-scope-mismatch"


def test_strict_verifier_binds_subject_audience_action_resource_and_request() -> None:
    issuer = CredentialIssuer(EXAMPLE_SECRET)
    claims = CredentialClaims(
        subject=PARENT_AGENT,
        audience=PUBLISH_SERVICE,
        action=ACTION,
        resource=RESOURCE_Q4,
        request_id=REQUEST_ID,
    )
    token = issuer.issue(claims)
    verifier = CredentialVerifier(issuer, mode=VerifierMode.STRICT)

    exact = ServiceRequest(
        caller=PARENT_AGENT,
        audience=PUBLISH_SERVICE,
        action=ACTION,
        resource=RESOURCE_Q4,
        request_id=REQUEST_ID,
    )
    variants = [
        ServiceRequest(CHILD_AGENT, PUBLISH_SERVICE, ACTION, RESOURCE_Q4, REQUEST_ID),
        ServiceRequest(PARENT_AGENT, STORAGE_SERVICE, ACTION, RESOURCE_Q4, REQUEST_ID),
        ServiceRequest(PARENT_AGENT, PUBLISH_SERVICE, "read", RESOURCE_Q4, REQUEST_ID),
        ServiceRequest(PARENT_AGENT, PUBLISH_SERVICE, ACTION, "report/executive", REQUEST_ID),
        ServiceRequest(PARENT_AGENT, PUBLISH_SERVICE, ACTION, RESOURCE_Q4, "request-002"),
    ]

    assert verifier.is_exactly_valid(exact, token) is True
    for variant in variants:
        assert verifier.is_exactly_valid(variant, token) is False


def test_tampered_credential_signature_is_rejected() -> None:
    issuer = CredentialIssuer(EXAMPLE_SECRET)
    token = issuer.issue(
        CredentialClaims(
            subject=PARENT_AGENT,
            audience=PUBLISH_SERVICE,
            action=ACTION,
            resource=RESOURCE_Q4,
            request_id=REQUEST_ID,
        )
    )
    payload, signature = token.split(".", 1)
    tampered = f"{payload}.{('0' if signature[0] != '0' else '1')}{signature[1:]}"

    assert issuer.decode_and_verify(tampered) is None


def test_result_evidence_omits_raw_credentials_and_secret() -> None:
    issuer = CredentialIssuer(EXAMPLE_SECRET)
    parent_token = issuer.issue(
        CredentialClaims(
            subject=PARENT_AGENT,
            audience=PUBLISH_SERVICE,
            action=ACTION,
            resource=RESOURCE_Q4,
            request_id=REQUEST_ID,
        )
    )
    result = run_credential_scope_lab(
        mode=LabMode.LEAKED_BOUND,
        secret=EXAMPLE_SECRET,
        run_id="test-evidence",
    )

    serialized = str(result.to_dict())
    assert parent_token not in serialized
    assert "lab05-example-secret" not in serialized
    assert len(result.parent_credential_sha256) == 64
    assert result.child_credential_sha256 is not None
    assert len(result.child_credential_sha256) == 64
