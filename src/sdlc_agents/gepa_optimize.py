"""Offline GEPA optimization of SDLC system prompts using Ollama via LiteLLM."""

from __future__ import annotations

import json
from pathlib import Path

import gepa
from gepa.adapters.default_adapter.default_adapter import EvaluationResult

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings
from sdlc_agents.gepa_report import (
    OptimizationReportCallback,
    RoleOptimizationTrace,
    write_combined_report,
    write_role_report,
)
from sdlc_agents.roles import get_role, optimizable_role_ids


def gepa_report_dir(settings: Settings) -> Path:
    return settings.gepa_report_dir


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


def optimize_role(settings: Settings, role: str) -> tuple[Path, RoleOptimizationTrace]:
    """Optimize one role's system prompt; write prompt + Markdown report."""
    role_cfg = get_role(role)
    dataset_path = settings.gepa_data_dir / role_cfg.gepa_dataset
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Missing GEPA dataset for role '{role}': {dataset_path}"
        )

    trainset = _load_dataset(dataset_path)
    valset = trainset

    seed_path = settings.prompts_seed_dir / f"{role_cfg.prompt_file}.txt"
    if not seed_path.exists():
        raise FileNotFoundError(f"Missing seed prompt for role '{role}': {seed_path}")
    seed_text = seed_path.read_text(encoding="utf-8").strip()
    seed_prompt = {"system_prompt": seed_text}

    print(f"  using task_lm={settings.gepa_task_lm}")
    print(f"  using reflection_lm={settings.gepa_reflection_lm}")

    trace = RoleOptimizationTrace(
        role=role,
        task_lm=settings.gepa_task_lm,
        reflection_lm=settings.gepa_reflection_lm,
        max_metric_calls=settings.gepa_max_metric_calls,
        seed_prompt=seed_text,
        trainset=trainset,
    )
    callback = OptimizationReportCallback(trace)

    run_dir = settings.gepa_runs_dir / role
    run_dir.mkdir(parents=True, exist_ok=True)

    result = gepa.optimize(
        seed_candidate=seed_prompt,
        trainset=trainset,
        valset=valset,
        task_lm=settings.gepa_task_lm,
        reflection_lm=settings.gepa_reflection_lm,
        evaluator=_case_insensitive_contains,
        max_metric_calls=settings.gepa_max_metric_calls,
        reflection_minibatch_size=settings.gepa_reflection_minibatch_size,
        candidate_selection_strategy=settings.gepa_candidate_selection_strategy,
        seed=settings.gepa_seed,
        display_progress_bar=settings.gepa_display_progress,
        callbacks=[callback],
        run_dir=str(run_dir),
    )

    best_gepa = result.best_candidate["system_prompt"]
    best_score = result.val_aggregate_scores[result.best_idx]
    seed_score = result.val_aggregate_scores[0] if result.val_aggregate_scores else 0.0

    if settings.gepa_prefer_seed_on_tie and best_score <= seed_score:
        best = seed_text
        selected_reason = (
            f"Kept seed prompt (GEPA best score {best_score:.3f} did not beat "
            f"seed score {seed_score:.3f}; GEPA_PREFER_SEED_ON_TIE=true)."
        )
    else:
        best = best_gepa
        selected_reason = (
            f"Selected GEPA candidate #{result.best_idx} "
            f"(val score {best_score:.3f}, seed {seed_score:.3f})."
        )

    trace.candidates = list(result.candidates)
    trace.val_scores = list(result.val_aggregate_scores)
    trace.best_idx = int(result.best_idx)
    trace.selected_prompt = best.strip()
    trace.selected_reason = selected_reason
    trace.total_metric_calls = result.total_metric_calls

    art.ensure_dirs(settings)
    settings.gepa_report_dir.mkdir(parents=True, exist_ok=True)
    out = settings.prompts_optimized_dir / f"{role}.txt"
    out.write_text(best.strip() + "\n", encoding="utf-8")

    report_path = write_role_report(trace, gepa_report_dir(settings))
    print(f"  best_idx={result.best_idx} best_score={best_score:.3f} seed_score={seed_score:.3f}")
    print(f"  report: {report_path}")
    return out, trace


def optimize_all_prompts(
    settings: Settings,
    roles: list[str] | tuple[str, ...] | None = None,
) -> list[Path]:
    """Optimize all (or selected) roles; return prompt paths written."""
    selected = tuple(roles) if roles else optimizable_role_ids()
    written: list[Path] = []
    traces: list[RoleOptimizationTrace] = []
    for role in selected:
        print(f"\n=== GEPA optimize: {role} ===")
        out, trace = optimize_role(settings, role)
        written.append(out)
        traces.append(trace)

    combined = write_combined_report(traces, gepa_report_dir(settings))
    print(f"\nCombined Markdown report: {combined}")
    return written
