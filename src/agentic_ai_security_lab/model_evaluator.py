"""Optional GenAI evaluator for Career Lab.

The deterministic evaluator remains the offline fallback. When OPENAI_API_KEY is
present, AASL can use the OpenAI Responses API to provide richer rubric-based
feedback, an improved answer, an exemplar answer, and a retry-to-mastery loop.

No API key is stored by AASL.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_MODEL = "gpt-6-luna"
DEFAULT_MASTERY_SCORE = 95


@dataclass(frozen=True)
class EvaluatorStatus:
    provider: str
    available: bool
    model: str | None
    mastery_score: int
    note: str


def evaluator_status() -> dict[str, Any]:
    provider = os.environ.get("AASL_EVAL_PROVIDER", "auto").strip().lower()
    api_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    model = os.environ.get("AASL_EVAL_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    mastery = int(os.environ.get("AASL_MASTERY_SCORE", str(DEFAULT_MASTERY_SCORE)))

    enabled = provider == "openai" or (provider == "auto" and api_key)
    if provider == "deterministic":
        enabled = False

    status = EvaluatorStatus(
        provider="openai" if enabled else "deterministic",
        available=enabled and api_key,
        model=model if enabled else None,
        mastery_score=max(80, min(100, mastery)),
        note=(
            "OpenAI Responses API evaluator enabled."
            if enabled and api_key
            else "Deterministic local evaluator active. Set OPENAI_API_KEY to enable GenAI evaluation."
        ),
    )
    return status.__dict__



def evaluation_weights(kind: str, level: str | None = None) -> dict[str, int]:
    """Return a 100-point rubric appropriate to the evaluation context."""

    if kind == "simulation":
        return {
            "technical_correctness": 35,
            "evidence_and_reasoning": 25,
            "remediation_or_decision_quality": 20,
            "completeness": 10,
            "communication": 10,
        }

    if level == "executive":
        return {
            "risk_judgment_and_tradeoffs": 25,
            "enterprise_scale_and_operating_model": 20,
            "executive_communication": 20,
            "technical_correctness": 15,
            "metrics_and_accountability": 10,
            "practicality": 10,
        }

    if level in {"principal", "manager"}:
        return {
            "technical_correctness": 25,
            "architecture_or_operating_model": 20,
            "risk_judgment_and_tradeoffs": 20,
            "scale_and_influence": 15,
            "metrics_and_outcomes": 10,
            "communication": 10,
        }

    return {
        "technical_correctness": 30,
        "depth_and_role_relevance": 20,
        "risk_judgment_and_tradeoffs": 15,
        "structure_and_communication": 15,
        "evidence_and_metrics": 10,
        "practicality": 10,
    }

def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    chunks: list[str] = []
    for item in payload.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _parse_json_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fence = chr(96) * 3
    if stripped.startswith(fence):
        stripped = stripped.strip(chr(96)).strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model did not return a JSON object")
    return json.loads(stripped[start : end + 1])


def _normalize_model_result(
    result: dict[str, Any],
    *,
    fallback: dict[str, Any],
    mastery_score: int,
) -> dict[str, Any]:
    score = int(result.get("score", fallback.get("score", 0)))
    score = max(0, min(100, score))
    mastered = score >= mastery_score

    def _list(name: str, fallback_name: str) -> list[str]:
        value = result.get(name)
        if isinstance(value, list):
            return [str(v) for v in value if str(v).strip()][:8]
        return [str(v) for v in fallback.get(fallback_name, [])][:8]

    model_answer = str(
        result.get("model_answer")
        or result.get("exemplar_answer")
        or fallback.get("model_answer", "")
    ).strip()
    improved_answer = str(
        result.get("improved_answer")
        or model_answer
        or fallback.get("model_answer", "")
    ).strip()

    return {
        **fallback,
        "score": score,
        "quality": str(result.get("quality") or fallback.get("quality", "")),
        "strengths": _list("strengths", "strengths"),
        "improvements": _list("improvements", "improvements"),
        "missing_concepts": _list("missing_concepts", "missing_concepts"),
        "model_answer": model_answer,
        "improved_answer": improved_answer,
        "mastered": mastered,
        "mastery_score": mastery_score,
        "retry_instruction": (
            "Mastered. Try another scenario or raise the role seniority."
            if mastered
            else str(
                result.get("retry_instruction")
                or "Revise your answer using the feedback, then submit again. Keep retrying until you reach mastery."
            )
        ),
        "evaluation_mode": "genai",
    }


def evaluate_with_openai(
    *,
    context: dict[str, Any],
    answer: str,
    fallback: dict[str, Any],
) -> dict[str, Any]:
    status = evaluator_status()
    if not status["available"]:
        score = int(fallback.get("score", 0))
        return {
            **fallback,
            "evaluation_mode": "deterministic",
            "mastery_score": status["mastery_score"],
            "mastered": score >= status["mastery_score"],
            "improved_answer": fallback.get("model_answer", ""),
            "retry_instruction": (
                "Mastered."
                if score >= status["mastery_score"]
                else "Revise the answer using the feedback and submit again."
            ),
            "rubric_weights": evaluation_weights(
                str(context.get("kind", "interview")),
                str(context.get("level", "")) or None,
            ),
        }

    api_key = os.environ["OPENAI_API_KEY"].strip()
    model = str(status["model"])
    mastery = int(status["mastery_score"])

    instructions = (
        "You are a rigorous but constructive cybersecurity interview and hands-on lab evaluator. "
        "Evaluate only the submitted answer against the supplied role, seniority, task, rubric, "
        "expected concepts, model answer, and security framework context. Do not reward buzzwords "
        "without correct reasoning. Distinguish technically wrong claims from merely missing depth. "
        "For senior, principal, manager, and executive levels, require decision quality, scale, "
        "tradeoffs, metrics, and communication appropriate to the level. Return JSON only."
    )
    weights = evaluation_weights(
        str(context.get("kind", "interview")),
        str(context.get("level", "")) or None,
    )
    prompt = {
        "evaluation_context": context,
        "rubric_weights_percent": weights,
        "learner_answer": answer,
        "deterministic_baseline": {
            "score": fallback.get("score"),
            "strengths": fallback.get("strengths"),
            "improvements": fallback.get("improvements"),
            "missing_concepts": fallback.get("missing_concepts"),
            "model_answer": fallback.get("model_answer"),
        },
        "mastery_score": mastery,
        "required_output": {
            "score": "integer 0-100",
            "quality": "short label",
            "strengths": ["specific strengths"],
            "improvements": ["critical but constructive improvements"],
            "missing_concepts": ["important missing concepts"],
            "improved_answer": "rewrite the learner answer into a stronger answer while preserving valid substance",
            "model_answer": "best exemplar answer appropriate to the role and seniority",
            "retry_instruction": "specific instruction for the next attempt",
        },
    }

    body = json.dumps(
        {
            "model": model,
            "instructions": instructions,
            "input": json.dumps(prompt, ensure_ascii=False),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        output_text = _extract_output_text(payload)
        parsed = _parse_json_text(output_text)
        normalized = _normalize_model_result(
            parsed,
            fallback=fallback,
            mastery_score=mastery,
        )
        normalized["model"] = model
        normalized["rubric_weights"] = weights
        return normalized
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        return {
            **fallback,
            "evaluation_mode": "deterministic-fallback",
            "evaluation_warning": f"GenAI evaluator unavailable: {exc}",
            "mastery_score": mastery,
            "mastered": int(fallback.get("score", 0)) >= mastery,
            "improved_answer": fallback.get("model_answer", ""),
            "retry_instruction": (
                "Revise the answer using the deterministic feedback and submit again."
            ),
            "rubric_weights": weights,
        }
