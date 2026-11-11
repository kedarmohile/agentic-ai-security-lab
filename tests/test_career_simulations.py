from pathlib import Path

from agentic_ai_security_lab.career_simulations import (
    ROLE_SCENARIOS,
    CareerAttemptStore,
    career_simulation_catalog,
    evaluate_interview_answer,
    evaluate_simulation_task,
)
from agentic_ai_security_lab.product_experiences import ROLE_TRACKS
from agentic_ai_security_lab.security_frameworks import framework_catalog
from agentic_ai_security_lab.vm_runtime import MultipassRuntime, blueprint_for_scenario, vm_catalog


def _role(role_id: str):
    return next(role for role in ROLE_TRACKS if role["role_id"] == role_id)


def test_framework_stack_contains_web_llm_agentic_and_atlas() -> None:
    catalog = framework_catalog()

    assert len(catalog["owasp_web_2025"]["items"]) == 10
    assert len(catalog["owasp_llm_2026"]["items"]) == 10
    assert len(catalog["owasp_agentic_2026"]["items"]) == 10
    assert len(catalog["mitre_atlas_agentic"]["items"]) >= 10

    web_ids = {item["id"] for item in catalog["owasp_web_2025"]["items"]}
    llm_ids = {item["id"] for item in catalog["owasp_llm_2026"]["items"]}
    agentic_ids = {item["id"] for item in catalog["owasp_agentic_2026"]["items"]}

    assert "A01:2025" in web_ids
    assert "A09:2025" in web_ids
    assert "LLM01:2026" in llm_ids
    assert "LLM03:2026" in llm_ids
    assert "ASI01" in agentic_ids
    assert "ASI10" in agentic_ids


def test_ai_security_role_has_atlas_and_owasp_mapped_simulations() -> None:
    data = career_simulation_catalog("ai-security")

    assert len(data["scenarios"]) >= 4
    assert data["frameworks"]["owasp_web_2025"]["items"]
    assert data["frameworks"]["owasp_llm_2026"]["items"]
    assert data["frameworks"]["owasp_agentic_2026"]["items"]

    scenario = next(
        item for item in data["scenarios"]
        if item["scenario_id"] == "sim-ai-agent-boundary"
    )
    assert scenario["specialization"] == "AI / Agentic Security Specialization"
    assert any(item["id"] == "AML.T0051" for item in scenario["atlas"])
    assert any(item["id"] == "LLM01:2026" for item in scenario["owasp_llm"])
    assert any(item["id"] == "ASI01" for item in scenario["owasp_agentic"])
    assert any(item["id"] == "A01:2025" for item in scenario["owasp_web"])


def test_appsec_role_keeps_general_owasp_coverage() -> None:
    data = career_simulation_catalog("appsec")
    scenario = next(
        item for item in data["scenarios"]
        if item["scenario_id"] == "sim-appsec-idor-review"
    )

    assert any(item["id"] == "A01:2025" for item in scenario["owasp_web"])
    assert scenario["owasp_llm"] == []
    assert scenario["owasp_agentic"] == []


def test_role_specific_scenarios_cover_requested_practice_types() -> None:
    assert "sim-log-hunt-token-reuse" in ROLE_SCENARIOS["soc-analyst"]
    assert "sim-auth-bypass-toy" in ROLE_SCENARIOS["red-team"]
    assert "sim-sensitive-data-discovery" in ROLE_SCENARIOS["appsec"]
    assert "sim-soar-playbook" in ROLE_SCENARIOS["soar-security-automation"]
    assert "sim-threat-intel-assessment" in ROLE_SCENARIOS["threat-intel"]
    assert "sim-ai-agent-boundary" in ROLE_SCENARIOS["ai-security"]


def test_simulation_evaluation_returns_score_feedback_and_model_answer() -> None:
    answer = (
        "evt-1040, evt-1041 and evt-1042 are the suspicious chain. "
        "The unknown device authenticated with mfa=false, reused token_id=TKN-77, "
        "then performed add_admin_role. I would revoke the token, contain the session, "
        "and build a detection that correlates the same request or token with privilege change."
    )
    result = evaluate_simulation_task(
        "sim-log-hunt-token-reuse",
        "hunt-chain",
        answer,
        hints_used=0,
    )

    assert result["score"] >= 75
    assert result["strengths"]
    assert isinstance(result["improvements"], list)
    assert len(result["model_answer"]) > 80
    assert "next_step" in result


def test_hints_reduce_simulation_score() -> None:
    answer = (
        "The X-Demo-Role header is caller-controlled. Supplying admin lets a valid "
        "low privilege session bypass authorization. The server must use trusted "
        "server-side session claims and authorization policy instead."
    )
    no_hints = evaluate_simulation_task(
        "sim-auth-bypass-toy",
        "bypass-analysis",
        answer,
        hints_used=0,
    )
    with_hints = evaluate_simulation_task(
        "sim-auth-bypass-toy",
        "bypass-analysis",
        answer,
        hints_used=2,
    )

    assert with_hints["score"] < no_hints["score"]
    assert with_hints["hint_penalty"] == 10


def test_interview_answer_evaluation_is_constructive() -> None:
    role = _role("ai-security")
    result = evaluate_interview_answer(
        role,
        "principal",
        "Architecture",
        "Design a secure operating model.",
        (
            "I would define trust boundaries, use workload identity and explicit authorization "
            "for privileged tools, preserve telemetry at every decision, design failure handling, "
            "and enforce least privilege around RAG, agents, and memory."
        ),
    )

    assert result["score"] > 0
    assert result["strengths"]
    assert result["improvements"]
    assert "model_answer" in result
    assert result["rubric"]["note"].startswith("Deterministic rubric")


def test_career_attempt_store_persists_feedback(tmp_path: Path) -> None:
    store = CareerAttemptStore(tmp_path)
    record = store.append(
        "simulation",
        {"scenario_id": "sim-ai-agent-boundary", "score": 88},
    )

    assert store.attempts()[0]["attempt_id"] == record["attempt_id"]
    assert store.attempts()[0]["score"] == 88


def test_vm_blueprints_are_git_portable_text_definitions() -> None:
    data = vm_catalog()

    assert data["provider"]["name"] == "Multipass"
    assert data["provider"]["host_platforms"] == ["Linux", "macOS", "Windows"]
    assert data["provider"]["reset_model"] == "destroy-and-recreate"
    assert len(data["blueprints"]) >= 3

    ids = {row["blueprint_id"] for row in data["blueprints"]}
    assert {"linux-soc-dfir", "linux-appsec", "linux-cloud-iam"}.issubset(ids)

    for scenario in (
        "sim-dfir-scope",
        "sim-sensitive-data-discovery",
        "sim-ai-agent-boundary",
    ):
        assert blueprint_for_scenario(scenario) is not None


def test_vm_runtime_does_not_require_multipass_for_catalog_or_status_detection() -> None:
    runtime = MultipassRuntime(binary="definitely-not-installed-aasl-multipass")
    assert runtime.available() is False
    info = runtime.host_info()
    assert info["available"] is False
    assert info["version"] is None
