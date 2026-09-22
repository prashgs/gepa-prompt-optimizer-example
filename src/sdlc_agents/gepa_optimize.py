"""Offline GEPA optimization of SDLC system prompts using Ollama via LiteLLM."""

from __future__ import annotations

import json
from pathlib import Path

import gepa
from gepa.adapters.default_adapter.default_adapter import EvaluationResult

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings

DEFAULT_ROLES = (
    "requirements",
    "design",
    "implement",
    "test",
    "review",
    "orchestrator",
)


def _load_dataset(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError(f"GEPA dataset must be a non-empty JSON list: {path}")
    return data


def _case_insensitive_contains(data: dict, response: str) -> EvaluationResult:
    """Score 1.0 when expected answer appears in the response (case-insensitive)."""
    answer = str(data["answer"])
    haystack = response.lower()
    needle = answer.lower()
    is_correct = needle in haystack
    score = 1.0 if is_correct else 0.0
    if is_correct:
        feedback = f"Correct: response includes '{answer}'."
    else:
        feedback = (
            f"Incorrect: response must include '{answer}' (case-insensitive). "
            "Keep the system prompt general for any SPA brief, and instruct the "
            "model to emit the required section headings or keywords."
        )
    return EvaluationResult(score=score, feedback=feedback, objective_scores=None)


def optimize_role(settings: Settings, role: str) -> Path:
    """Optimize one role's system prompt and write prompts/optimized/<role>.txt."""
    dataset_path = settings.gepa_data_dir / f"{role}.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Missing GEPA dataset for role '{role}': {dataset_path}")

    trainset = _load_dataset(dataset_path)
    # Tiny valset: reuse train examples (local demo budget)
    valset = trainset

    seed_path = settings.prompts_seed_dir / f"{role}.txt"
    seed_text = seed_path.read_text(encoding="utf-8").strip()
    seed_prompt = {"system_prompt": seed_text}

    result = gepa.optimize(
        seed_candidate=seed_prompt,
        trainset=trainset,
        valset=valset,
        task_lm=settings.gepa_task_lm,
        reflection_lm=settings.gepa_reflection_lm,
        evaluator=_case_insensitive_contains,
        max_metric_calls=settings.gepa_max_metric_calls,
        display_progress_bar=True,
    )

    best = result.best_candidate["system_prompt"]
    best_score = result.val_aggregate_scores[result.best_idx]
    seed_score = result.val_aggregate_scores[0] if result.val_aggregate_scores else 0.0
    # Prefer seed when optimization did not improve validation score
    if best_score <= seed_score:
        best = seed_text

    art.ensure_dirs(settings)
    out = settings.prompts_optimized_dir / f"{role}.txt"
    out.write_text(best.strip() + "\n", encoding="utf-8")
    print(f"  best_idx={result.best_idx} best_score={best_score:.3f} seed_score={seed_score:.3f}")
    return out


def optimize_all_prompts(
    settings: Settings,
    roles: list[str] | tuple[str, ...] | None = None,
) -> list[Path]:
    """Optimize all (or selected) roles; return paths written."""
    selected = tuple(roles) if roles else DEFAULT_ROLES
    written: list[Path] = []
    for role in selected:
        print(f"\n=== GEPA optimize: {role} ===")
        written.append(optimize_role(settings, role))
    return written
