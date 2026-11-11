"""Lab 05: agent identity and credential scope leakage.

Credentials, services, and actions are synthetic. The runtime is an in-memory
ledger and performs no network, shell, cloud, or external service operation.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from enum import Enum


LAB_ID = "lab05-agent-credential-scope-leakage"
PARENT_AGENT = "agent-a"
CHILD_AGENT = "agent-b"
PUBLISH_SERVICE = "publisher-service"
STORAGE_SERVICE = "storage-service"
ACTION = "publish"
RESOURCE_Q4 = "report/Q4"
RESOURCE_EXECUTIVE = "report/executive"
REQUEST_ID = "request-001"


class VerifierMode(str, Enum):
    """How the synthetic service validates a credential."""

    STRICT = "strict"
    BEARER_SCOPE_ONLY = "bearer-scope-only"


class LabMode(str, Enum):
    """Deterministic Lab 05 scenarios."""

    SECURE = "secure"
    LEAKED_BOUND = "leaked-bound"
    VULNERABLE = "vulnerable"
    DERIVED_CHILD = "derived-child"
    AUDIENCE_SUBSTITUTION = "audience-substitution"
    RESOURCE_SUBSTITUTION = "resource-substitution"
    REQUEST_REPLAY = "request-replay"


class Verdict(str, Enum):
    """Outcome of the credential-boundary test."""

    PASS = "pass"
    FAIL = "fail"
    EXPECTED_AUTHORIZED = "expected-authorized"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class CredentialClaims:
    """Claims bound into one synthetic credential."""

    subject: str
    audience: str
    action: str
    resource: str
    request_id: str

    def canonical_payload(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ServiceRequest:
    """Request made by an agent to a synthetic service."""

    caller: str
    audience: str
    action: str
    resource: str
    request_id: str

    def sha256(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


class CredentialIssuer:
    """Issue and cryptographically verify synthetic scoped credentials."""

    def __init__(self, secret: bytes) -> None:
        if not secret:
            raise ValueError("credential secret must not be empty")
        self._secret = secret

    def issue(self, claims: CredentialClaims) -> str:
        payload = _b64url_encode(claims.canonical_payload().encode("utf-8"))
        signature = hmac.new(
            self._secret,
            payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        return f"{payload}.{signature}"

    def decode_and_verify(self, token: str | None) -> CredentialClaims | None:
        if token is None:
            return None
        try:
            payload, supplied_signature = token.split(".", 1)
            expected_signature = hmac.new(
                self._secret,
                payload.encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected_signature, supplied_signature):
                return None
            raw = json.loads(_b64url_decode(payload).decode("utf-8"))
            return CredentialClaims(**raw)
        except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
            return None


@dataclass(frozen=True)
class ServiceDecision:
    """Synthetic service authorization decision."""

    allowed: bool
    reason: str


class CredentialVerifier:
    """Validate credential signature and scope at a service boundary."""

    def __init__(
        self,
        issuer: CredentialIssuer,
        *,
        mode: VerifierMode = VerifierMode.STRICT,
    ) -> None:
        self.issuer = issuer
        self.mode = mode

    def is_exactly_valid(self, request: ServiceRequest, token: str | None) -> bool:
        """Return whether every identity/scope dimension matches."""
        claims = self.issuer.decode_and_verify(token)
        if claims is None:
            return False
        return (
            claims.subject == request.caller
            and claims.audience == request.audience
            and claims.action == request.action
            and claims.resource == request.resource
            and claims.request_id == request.request_id
        )

    def authorize(self, request: ServiceRequest, token: str | None) -> ServiceDecision:
        claims = self.issuer.decode_and_verify(token)
        if claims is None:
            return ServiceDecision(False, "missing-or-invalid-credential")

        if (
            claims.audience != request.audience
            or claims.action != request.action
            or claims.resource != request.resource
            or claims.request_id != request.request_id
        ):
            return ServiceDecision(False, "credential-scope-mismatch")

        if self.mode is VerifierMode.STRICT and claims.subject != request.caller:
            return ServiceDecision(False, "credential-subject-mismatch")

        if self.mode is VerifierMode.BEARER_SCOPE_ONLY:
            return ServiceDecision(True, "bearer-scope-accepted")

        return ServiceDecision(True, "strict-scope-accepted")


class SyntheticServiceRuntime:
    """In-memory service ledger with no external side effects."""

    def __init__(self, verifier: CredentialVerifier) -> None:
        self.verifier = verifier
        self.executed: list[ServiceRequest] = []

    def invoke(self, request: ServiceRequest, token: str | None) -> ServiceDecision:
        decision = self.verifier.authorize(request, token)
        if decision.allowed:
            self.executed.append(request)
        return decision


@dataclass(frozen=True)
class CredentialScopeResult:
    """Structured evidence emitted by Lab 05."""

    lab: str
    run_id: str
    lab_mode: str
    verifier_mode: str
    owner_control_succeeded: bool
    parent_credential_exposed_to_child: bool
    child_received_credential: bool
    child_credential_is_parent_token: bool
    credential_exactly_valid_for_child_request: bool
    child_action_attempted: bool
    child_action_executed: bool
    decision_reason: str
    exposure_finding: bool
    unauthorized_use_finding: bool
    finding: bool
    verdict: str
    severity: str
    request_sha256: str
    child_credential_sha256: str | None
    parent_credential_sha256: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parent_claims() -> CredentialClaims:
    return CredentialClaims(
        subject=PARENT_AGENT,
        audience=PUBLISH_SERVICE,
        action=ACTION,
        resource=RESOURCE_Q4,
        request_id=REQUEST_ID,
    )


def _child_request(mode: LabMode) -> ServiceRequest:
    audience = STORAGE_SERVICE if mode is LabMode.AUDIENCE_SUBSTITUTION else PUBLISH_SERVICE
    resource = RESOURCE_EXECUTIVE if mode is LabMode.RESOURCE_SUBSTITUTION else RESOURCE_Q4
    request_id = "request-002" if mode is LabMode.REQUEST_REPLAY else REQUEST_ID
    return ServiceRequest(
        caller=CHILD_AGENT,
        audience=audience,
        action=ACTION,
        resource=resource,
        request_id=request_id,
    )


def _child_token(
    mode: LabMode,
    issuer: CredentialIssuer,
    parent_token: str,
    child_request: ServiceRequest,
) -> tuple[str | None, bool]:
    """Return child credential and whether the raw parent token crossed boundary."""

    if mode is LabMode.SECURE:
        return None, False

    if mode in {LabMode.LEAKED_BOUND, LabMode.VULNERABLE}:
        return parent_token, True

    if mode is LabMode.DERIVED_CHILD:
        claims = CredentialClaims(
            subject=CHILD_AGENT,
            audience=child_request.audience,
            action=child_request.action,
            resource=child_request.resource,
            request_id=child_request.request_id,
        )
        return issuer.issue(claims), False

    if mode is LabMode.AUDIENCE_SUBSTITUTION:
        claims = CredentialClaims(
            subject=CHILD_AGENT,
            audience=PUBLISH_SERVICE,
            action=ACTION,
            resource=RESOURCE_Q4,
            request_id=REQUEST_ID,
        )
        return issuer.issue(claims), False

    if mode is LabMode.RESOURCE_SUBSTITUTION:
        claims = CredentialClaims(
            subject=CHILD_AGENT,
            audience=PUBLISH_SERVICE,
            action=ACTION,
            resource=RESOURCE_Q4,
            request_id=REQUEST_ID,
        )
        return issuer.issue(claims), False

    claims = CredentialClaims(
        subject=CHILD_AGENT,
        audience=PUBLISH_SERVICE,
        action=ACTION,
        resource=RESOURCE_Q4,
        request_id=REQUEST_ID,
    )
    return issuer.issue(claims), False


def run_credential_scope_lab(
    *,
    mode: LabMode = LabMode.SECURE,
    secret: bytes | None = None,
    run_id: str | None = None,
) -> CredentialScopeResult:
    """Run the agent credential exposure and scope test."""

    issuer = CredentialIssuer(secret or secrets.token_bytes(32))
    parent_token = issuer.issue(_parent_claims())

    strict_verifier = CredentialVerifier(issuer, mode=VerifierMode.STRICT)
    owner_runtime = SyntheticServiceRuntime(strict_verifier)
    owner_request = ServiceRequest(
        caller=PARENT_AGENT,
        audience=PUBLISH_SERVICE,
        action=ACTION,
        resource=RESOURCE_Q4,
        request_id=REQUEST_ID,
    )
    owner_decision = owner_runtime.invoke(owner_request, parent_token)
    owner_control_succeeded = (
        owner_decision.allowed and owner_request in owner_runtime.executed
    )

    child_request = _child_request(mode)
    token, parent_exposed = _child_token(
        mode,
        issuer,
        parent_token,
        child_request,
    )

    verifier_mode = (
        VerifierMode.BEARER_SCOPE_ONLY
        if mode is LabMode.VULNERABLE
        else VerifierMode.STRICT
    )
    verifier = CredentialVerifier(issuer, mode=verifier_mode)
    runtime = SyntheticServiceRuntime(verifier)

    exact_valid = verifier.is_exactly_valid(child_request, token)
    decision = runtime.invoke(child_request, token)
    child_executed = child_request in runtime.executed

    exposure_finding = parent_exposed
    unauthorized_use_finding = child_executed and not exact_valid
    finding = exposure_finding or unauthorized_use_finding

    if not owner_control_succeeded:
        verdict = Verdict.INCONCLUSIVE
        severity = "none"
        finding = False
        exposure_finding = False
        unauthorized_use_finding = False
    elif mode is LabMode.DERIVED_CHILD and exact_valid and child_executed:
        verdict = Verdict.EXPECTED_AUTHORIZED
        severity = "none"
    elif unauthorized_use_finding:
        verdict = Verdict.FAIL
        severity = "high"
    elif exposure_finding:
        verdict = Verdict.FAIL
        severity = "medium"
    elif child_executed and exact_valid:
        verdict = Verdict.EXPECTED_AUTHORIZED
        severity = "none"
    else:
        verdict = Verdict.PASS
        severity = "none"

    return CredentialScopeResult(
        lab=LAB_ID,
        run_id=run_id or secrets.token_hex(8),
        lab_mode=mode.value,
        verifier_mode=verifier_mode.value,
        owner_control_succeeded=owner_control_succeeded,
        parent_credential_exposed_to_child=parent_exposed,
        child_received_credential=token is not None,
        child_credential_is_parent_token=token == parent_token if token is not None else False,
        credential_exactly_valid_for_child_request=exact_valid,
        child_action_attempted=True,
        child_action_executed=child_executed,
        decision_reason=decision.reason,
        exposure_finding=exposure_finding,
        unauthorized_use_finding=unauthorized_use_finding,
        finding=finding,
        verdict=verdict.value,
        severity=severity,
        request_sha256=child_request.sha256(),
        child_credential_sha256=_sha256(token) if token is not None else None,
        parent_credential_sha256=_sha256(parent_token),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Lab 05: agent credential scope leakage."
    )
    parser.add_argument(
        "--mode",
        choices=tuple(mode.value for mode in LabMode),
        default=LabMode.SECURE.value,
        help="Deterministic credential-boundary scenario to exercise.",
    )
    args = parser.parse_args()

    result = run_credential_scope_lab(mode=LabMode(args.mode))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 1 if result.finding else 0


if __name__ == "__main__":
    raise SystemExit(main())
