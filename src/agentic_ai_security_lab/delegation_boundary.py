"""Lab 04: confused-deputy delegation in multi-agent systems.

All actions are simulated in memory. The lab tests whether a privileged deputy
checks the original principal's delegation instead of relying on the deputy's
own local capability as authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from enum import Enum


LAB_ID = "lab04-confused-deputy-delegation"
PRINCIPAL_ID = "principal-alice"
DELEGATE_ID = "agent-a"
ALTERNATE_DELEGATE_ID = "agent-c"
DEPUTY_ID = "agent-b"
ACTION_READ = "read"
ACTION_PUBLISH = "publish"
RESOURCE_Q4 = "report/Q4"
RESOURCE_EXECUTIVE = "report/executive"


class BrokerMode(str, Enum):
    """How the deputy broker evaluates authority."""

    SECURE = "secure"
    TRUST_DEPUTY_LOCAL_PRIVILEGE = "trust-deputy-local-privilege"


class LabMode(str, Enum):
    """Deterministic Lab 04 scenarios."""

    SECURE = "secure"
    VULNERABLE = "vulnerable"
    EXACT_DELEGATED = "exact-delegated"
    RESOURCE_SUBSTITUTION = "resource-substitution"
    DELEGATE_SUBSTITUTION = "delegate-substitution"
    REQUEST_REPLAY = "request-replay"


class Verdict(str, Enum):
    """Outcome of the delegation-boundary test."""

    PASS = "pass"
    FAIL = "fail"
    EXPECTED_AUTHORIZED = "expected-authorized"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class DelegatedAction:
    """One action requested through a delegation chain."""

    principal_id: str
    delegate_id: str
    deputy_id: str
    request_id: str
    action: str
    resource: str

    def canonical_payload(self) -> str:
        """Stable payload used for signed delegation and evidence hashing."""
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def sha256(self) -> str:
        """Fingerprint the exact delegated action."""
        return hashlib.sha256(self.canonical_payload().encode("utf-8")).hexdigest()


class DelegationAuthority:
    """Issue and verify delegation grants bound to an exact action chain."""

    def __init__(self, secret: bytes) -> None:
        if not secret:
            raise ValueError("delegation secret must not be empty")
        self._secret = secret

    def issue(self, action: DelegatedAction) -> str:
        """Issue a deterministic HMAC grant for the exact delegated action."""
        return hmac.new(
            self._secret,
            action.canonical_payload().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify(self, action: DelegatedAction, token: str | None) -> bool:
        """Verify the complete principal/delegate/deputy/action binding."""
        if token is None:
            return False
        expected = self.issue(action)
        return hmac.compare_digest(expected, token)


@dataclass(frozen=True)
class DeputyCapabilityPolicy:
    """Local capabilities held by the privileged deputy."""

    deputy_id: str
    capabilities: frozenset[tuple[str, str]]

    def can(self, deputy_id: str, action: str, resource: str) -> bool:
        """Return whether this deputy locally possesses the capability."""
        return (
            deputy_id == self.deputy_id
            and (action, resource) in self.capabilities
        )


@dataclass(frozen=True)
class DelegationDecision:
    """Authorization decision for a delegated action."""

    allowed: bool
    source: str
    reason: str


class DelegationBroker:
    """Combine deputy capability with original-principal delegation."""

    def __init__(
        self,
        authority: DelegationAuthority,
        deputy_policy: DeputyCapabilityPolicy,
        *,
        mode: BrokerMode = BrokerMode.SECURE,
    ) -> None:
        self.authority = authority
        self.deputy_policy = deputy_policy
        self.mode = mode

    def authorize(
        self,
        request: DelegatedAction,
        delegation_token: str | None,
    ) -> DelegationDecision:
        """Authorize only when both local capability and delegation allow it."""

        if not self.deputy_policy.can(
            request.deputy_id,
            request.action,
            request.resource,
        ):
            return DelegationDecision(
                allowed=False,
                source="none",
                reason="deputy-lacks-local-capability",
            )

        if self.authority.verify(request, delegation_token):
            return DelegationDecision(
                allowed=True,
                source="delegation-grant",
                reason="valid-bound-delegation",
            )

        if self.mode is BrokerMode.TRUST_DEPUTY_LOCAL_PRIVILEGE:
            return DelegationDecision(
                allowed=True,
                source="deputy-local-privilege",
                reason="deputy-capability-treated-as-principal-authority",
            )

        return DelegationDecision(
            allowed=False,
            source="none",
            reason="delegation-does-not-authorize-request",
        )


class SimulatedDeputyRuntime:
    """In-memory action ledger with no external side effects."""

    def __init__(self, broker: DelegationBroker) -> None:
        self.broker = broker
        self.decisions: list[tuple[DelegatedAction, DelegationDecision]] = []
        self.executed: list[DelegatedAction] = []

    def invoke(
        self,
        request: DelegatedAction,
        delegation_token: str | None,
    ) -> DelegationDecision:
        """Authorize and record a simulated delegated action."""
        decision = self.broker.authorize(request, delegation_token)
        self.decisions.append((request, decision))
        if decision.allowed:
            self.executed.append(request)
        return decision


@dataclass(frozen=True)
class DelegationBoundaryResult:
    """Structured evidence emitted by Lab 04."""

    lab: str
    run_id: str
    lab_mode: str
    broker_mode: str
    principal_id: str
    delegate_id: str
    deputy_id: str
    requested_action: str
    requested_resource: str
    control_delegation_succeeded: bool
    deputy_has_local_capability: bool
    delegation_token_supplied: bool
    delegation_valid_for_request: bool
    delegated_action_attempted: bool
    delegated_action_executed: bool
    authorization_source: str
    decision_reason: str
    finding: bool
    verdict: str
    severity: str
    request_sha256: str
    delegation_token_sha256: str | None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable result."""
        return asdict(self)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _deputy_policy() -> DeputyCapabilityPolicy:
    return DeputyCapabilityPolicy(
        deputy_id=DEPUTY_ID,
        capabilities=frozenset(
            {
                (ACTION_READ, RESOURCE_Q4),
                (ACTION_PUBLISH, RESOURCE_Q4),
                (ACTION_PUBLISH, RESOURCE_EXECUTIVE),
            }
        ),
    )


def _target_request(mode: LabMode) -> DelegatedAction:
    delegate_id = (
        ALTERNATE_DELEGATE_ID
        if mode is LabMode.DELEGATE_SUBSTITUTION
        else DELEGATE_ID
    )
    resource = (
        RESOURCE_EXECUTIVE
        if mode is LabMode.RESOURCE_SUBSTITUTION
        else RESOURCE_Q4
    )
    return DelegatedAction(
        principal_id=PRINCIPAL_ID,
        delegate_id=delegate_id,
        deputy_id=DEPUTY_ID,
        request_id="request-001",
        action=ACTION_PUBLISH,
        resource=resource,
    )


def _grant_for_scenario(
    mode: LabMode,
    target: DelegatedAction,
) -> DelegatedAction:
    """Return the action scope actually granted by the principal."""

    if mode in {LabMode.SECURE, LabMode.VULNERABLE}:
        return DelegatedAction(
            principal_id=PRINCIPAL_ID,
            delegate_id=DELEGATE_ID,
            deputy_id=DEPUTY_ID,
            request_id=target.request_id,
            action=ACTION_READ,
            resource=RESOURCE_Q4,
        )

    if mode is LabMode.RESOURCE_SUBSTITUTION:
        return DelegatedAction(
            principal_id=PRINCIPAL_ID,
            delegate_id=DELEGATE_ID,
            deputy_id=DEPUTY_ID,
            request_id=target.request_id,
            action=ACTION_PUBLISH,
            resource=RESOURCE_Q4,
        )

    if mode is LabMode.DELEGATE_SUBSTITUTION:
        return DelegatedAction(
            principal_id=PRINCIPAL_ID,
            delegate_id=DELEGATE_ID,
            deputy_id=DEPUTY_ID,
            request_id=target.request_id,
            action=ACTION_PUBLISH,
            resource=target.resource,
        )

    if mode is LabMode.REQUEST_REPLAY:
        return DelegatedAction(
            principal_id=PRINCIPAL_ID,
            delegate_id=DELEGATE_ID,
            deputy_id=DEPUTY_ID,
            request_id="request-previous",
            action=ACTION_PUBLISH,
            resource=target.resource,
        )

    return target


def run_delegation_boundary_lab(
    *,
    mode: LabMode = LabMode.SECURE,
    secret: bytes | None = None,
    run_id: str | None = None,
) -> DelegationBoundaryResult:
    """Run the confused-deputy delegation-boundary test."""

    authority = DelegationAuthority(secret or secrets.token_bytes(32))
    deputy_policy = _deputy_policy()
    broker_mode = (
        BrokerMode.TRUST_DEPUTY_LOCAL_PRIVILEGE
        if mode is LabMode.VULNERABLE
        else BrokerMode.SECURE
    )
    broker = DelegationBroker(
        authority,
        deputy_policy,
        mode=broker_mode,
    )
    runtime = SimulatedDeputyRuntime(broker)

    control_request = DelegatedAction(
        principal_id=PRINCIPAL_ID,
        delegate_id=DELEGATE_ID,
        deputy_id=DEPUTY_ID,
        request_id="control-001",
        action=ACTION_READ,
        resource=RESOURCE_Q4,
    )
    control_token = authority.issue(control_request)
    control_decision = runtime.invoke(control_request, control_token)
    control_delegation_succeeded = (
        control_decision.allowed and control_request in runtime.executed
    )

    target = _target_request(mode)
    grant = _grant_for_scenario(mode, target)
    delegation_token = authority.issue(grant)

    deputy_has_local_capability = deputy_policy.can(
        target.deputy_id,
        target.action,
        target.resource,
    )
    delegation_valid_for_request = authority.verify(target, delegation_token)

    decision = runtime.invoke(target, delegation_token)
    delegated_action_executed = target in runtime.executed

    if not control_delegation_succeeded or not deputy_has_local_capability:
        verdict = Verdict.INCONCLUSIVE
        finding = False
        severity = "none"
    elif delegation_valid_for_request:
        if delegated_action_executed:
            verdict = Verdict.EXPECTED_AUTHORIZED
            finding = False
            severity = "none"
        else:
            verdict = Verdict.INCONCLUSIVE
            finding = False
            severity = "none"
    elif delegated_action_executed:
        verdict = Verdict.FAIL
        finding = True
        severity = "high"
    else:
        verdict = Verdict.PASS
        finding = False
        severity = "none"

    return DelegationBoundaryResult(
        lab=LAB_ID,
        run_id=run_id or secrets.token_hex(8),
        lab_mode=mode.value,
        broker_mode=broker_mode.value,
        principal_id=target.principal_id,
        delegate_id=target.delegate_id,
        deputy_id=target.deputy_id,
        requested_action=target.action,
        requested_resource=target.resource,
        control_delegation_succeeded=control_delegation_succeeded,
        deputy_has_local_capability=deputy_has_local_capability,
        delegation_token_supplied=True,
        delegation_valid_for_request=delegation_valid_for_request,
        delegated_action_attempted=True,
        delegated_action_executed=delegated_action_executed,
        authorization_source=decision.source,
        decision_reason=decision.reason,
        finding=finding,
        verdict=verdict.value,
        severity=severity,
        request_sha256=target.sha256(),
        delegation_token_sha256=_sha256(delegation_token),
    )


def main() -> int:
    """CLI entry point for Lab 04."""
    parser = argparse.ArgumentParser(
        description="Run Lab 04: confused-deputy delegation boundary."
    )
    parser.add_argument(
        "--mode",
        choices=tuple(mode.value for mode in LabMode),
        default=LabMode.SECURE.value,
        help="Deterministic delegation scenario to exercise.",
    )
    args = parser.parse_args()

    result = run_delegation_boundary_lab(mode=LabMode(args.mode))
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 1 if result.finding else 0


if __name__ == "__main__":
    raise SystemExit(main())
