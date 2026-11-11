import os
import re
from pathlib import Path

import pytest

from agentic_ai_security_lab.model_evaluator import (
    _normalize_model_result,
    evaluate_with_openai,
    evaluation_weights,
    evaluator_status,
)
from agentic_ai_security_lab.career_simulations import CareerAttemptStore
from agentic_ai_security_lab.product_experiences import (
    INTERVIEWER_PERSONAS,
    LEVEL_PROFILES,
    career_catalog,
    interview_session,
)


def test_all_career_levels_have_explicit_profiles() -> None:
    expected = {"entry", "mid", "senior", "principal", "manager", "executive"}
    assert set(LEVEL_PROFILES) == expected

    catalog = career_catalog()
    assert set(catalog["levels"]) == expected
    assert len(catalog["interviewers"]) >= 4


@pytest.mark.parametrize(
    ("level", "minimum_questions"),
    [
        ("entry", 8),
        ("mid", 8),
        ("senior", 8),
        ("principal", 10),
        ("manager", 10),
        ("executive", 11),
    ],
)
def test_each_seniority_level_generates_a_session(level: str, minimum_questions: int) -> None:
    session = interview_session("ai-security", level)

    assert session["level"] == level
    assert session["level_profile"]["label"].lower() == level
    assert len(session["questions"]) >= minimum_questions
    assert session["interviewers"]


def test_principal_and_executive_are_materially_different() -> None:
    principal = interview_session("security-architecture", "principal")
    executive = interview_session("security-architecture", "executive")

    principal_questions = " ".join(row["question"] for row in principal["questions"]).lower()
    executive_questions = " ".join(row["question"] for row in executive["questions"]).lower()

    assert "reference architecture" in principal_questions
    assert "board" in executive_questions
    assert "budget" in executive_questions
    assert "20%" in executive_questions


def test_interviewer_personas_are_distinct() -> None:
    ids = {row["persona_id"] for row in INTERVIEWER_PERSONAS}
    names = {row["name"] for row in INTERVIEWER_PERSONAS}

    assert len(ids) == len(INTERVIEWER_PERSONAS)
    assert len(names) == len(INTERVIEWER_PERSONAS)
    assert all(row["style"] for row in INTERVIEWER_PERSONAS)


def test_evaluator_defaults_to_deterministic_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AASL_EVAL_PROVIDER", raising=False)
    monkeypatch.delenv("AASL_EVAL_MODEL", raising=False)

    status = evaluator_status()

    assert status["provider"] == "deterministic"
    assert status["available"] is False
    assert status["mastery_score"] == 95


def test_deterministic_fallback_supports_retry_to_mastery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AASL_EVAL_PROVIDER", "auto")

    fallback = {
        "score": 72,
        "quality": "Developing",
        "strengths": ["Covered: authorization"],
        "improvements": ["Add scale and metrics."],
        "missing_concepts": ["metrics"],
        "model_answer": "A stronger exemplar answer.",
    }
    result = evaluate_with_openai(
        context={"kind": "interview", "level": "principal"},
        answer="My answer",
        fallback=fallback,
    )

    assert result["evaluation_mode"] == "deterministic"
    assert result["mastered"] is False
    assert result["mastery_score"] == 95
    assert result["improved_answer"] == fallback["model_answer"]
    assert "Revise" in result["retry_instruction"]


def test_model_result_normalization_returns_mastery_and_improved_answer() -> None:
    fallback = {
        "score": 60,
        "quality": "Developing",
        "strengths": [],
        "improvements": [],
        "missing_concepts": [],
        "model_answer": "Fallback exemplar",
    }
    result = _normalize_model_result(
        {
            "score": 97,
            "quality": "Excellent",
            "strengths": ["Clear architecture"],
            "improvements": ["Tighten opening"],
            "missing_concepts": [],
            "improved_answer": "Improved learner answer",
            "model_answer": "Best exemplar answer",
            "retry_instruction": "Move on",
        },
        fallback=fallback,
        mastery_score=95,
    )

    assert result["mastered"] is True
    assert result["score"] == 97
    assert result["improved_answer"] == "Improved learner answer"
    assert result["model_answer"] == "Best exemplar answer"
    assert result["evaluation_mode"] == "genai"


def test_console_js_avoids_single_selector_foreach_runtime_bug() -> None:
    js = Path("src/agentic_ai_security_lab/console_assets/app.js").read_text(encoding="utf-8")

    # $() returns one element; only $$() may be iterated.
    assert not re.search(r"(?<!\$)\$\([^\n;]*\)\.forEach", js)
    assert 'boot().then(bootV2)' in js
    assert '$$(".career-mode-tab").forEach' in js
    assert '$$("[data-scroll-target]").forEach' in js


def test_career_ui_contains_mastery_persona_and_voice_controls() -> None:
    html = Path("src/agentic_ai_security_lab/console_assets/index.html").read_text(encoding="utf-8")
    js = Path("src/agentic_ai_security_lab/console_assets/app.js").read_text(encoding="utf-8")

    assert 'id="career-evaluator-status"' in html
    assert 'id="career-interviewer"' in html
    assert 'id="career-level-expectation"' in html
    assert "Ask aloud" in js
    assert "Answer by voice" in js
    assert "SpeechRecognition" in js
    assert "speechSynthesis" in js


def test_typography_uses_semantic_type_scale() -> None:
    css = Path("src/agentic_ai_security_lab/console_assets/styles.css").read_text(encoding="utf-8")

    for token in (
        "--type-micro",
        "--type-label",
        "--type-body",
        "--type-body-lg",
        "--type-h3",
        "--type-h2",
        "--type-h1",
        "--type-display",
    ):
        assert token in css



def test_weighted_rubrics_sum_to_one_hundred() -> None:
    for kind, level in (
        ("interview", "senior"),
        ("interview", "principal"),
        ("interview", "manager"),
        ("interview", "executive"),
        ("simulation", None),
    ):
        weights = evaluation_weights(kind, level)
        assert sum(weights.values()) == 100


def test_attempt_store_tracks_retry_progress(tmp_path: Path) -> None:
    store = CareerAttemptStore(tmp_path)

    first = store.append(
        "interview",
        {
            "role_id": "ai-security",
            "level": "principal",
            "dimension": "Architecture",
            "question": "Design the boundary.",
            "score": 71,
        },
    )
    second = store.append(
        "interview",
        {
            "role_id": "ai-security",
            "level": "principal",
            "dimension": "Architecture",
            "question": "Design the boundary.",
            "score": 89,
        },
    )

    assert first["attempt_number"] == 1
    assert first["previous_best_score"] == 0
    assert first["best_score"] == 71

    assert second["attempt_number"] == 2
    assert second["previous_best_score"] == 71
    assert second["best_score"] == 89
    assert second["score_delta_from_previous_best"] == 18


def test_genai_path_can_be_exercised_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return (
                b'{"output":[{"content":[{"type":"output_text","text":"'
                b'{\\\"score\\\":96,\\\"quality\\\":\\\"Excellent\\\",'
                b'\\\"strengths\\\":[\\\"Clear tradeoff\\\"],'
                b'\\\"improvements\\\":[\\\"Tighten opening\\\"],'
                b'\\\"missing_concepts\\\":[],'
                b'\\\"improved_answer\\\":\\\"Improved answer\\\",'
                b'\\\"model_answer\\\":\\\"Exemplar answer\\\",'
                b'\\\"retry_instruction\\\":\\\"Mastered\\\"}"}]}]}'
            )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AASL_EVAL_PROVIDER", "openai")
    monkeypatch.setenv("AASL_EVAL_MODEL", "gpt-6-luna")
    monkeypatch.setattr(
        "agentic_ai_security_lab.model_evaluator.urllib.request.urlopen",
        lambda request, timeout=60: FakeResponse(),
    )

    result = evaluate_with_openai(
        context={"kind": "interview", "level": "executive"},
        answer="A strong answer",
        fallback={
            "score": 70,
            "quality": "Developing",
            "strengths": [],
            "improvements": [],
            "missing_concepts": [],
            "model_answer": "Fallback",
        },
    )

    assert result["evaluation_mode"] == "genai"
    assert result["model"] == "gpt-6-luna"
    assert result["score"] == 96
    assert result["mastered"] is True
    assert result["improved_answer"] == "Improved answer"
    assert sum(result["rubric_weights"].values()) == 100



def test_career_selects_are_compact_and_actions_remain_visible() -> None:
    css = Path("src/agentic_ai_security_lab/console_assets/styles.css").read_text(encoding="utf-8")
    html = Path("src/agentic_ai_security_lab/console_assets/index.html").read_text(encoding="utf-8")

    assert ".interview-controls select" in css
    assert "font-size:var(--type-label)" in css
    assert ".interview-controls-expanded #generate-interview" in css
    assert "grid-column:1 / -1" in css
    assert ".simulation-controls #load-simulation" in css
    assert "ENGINE v0.10" in html
