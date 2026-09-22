"""Load settings from environment / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Project root: .../gepa-prompt-optimizer-example
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    ollama_host: str
    orchestrator_model: str
    worker_model: str
    gepa_task_lm: str
    gepa_reflection_lm: str
    gepa_max_metric_calls: int
    gepa_data_dir: Path
    gepa_runs_dir: Path
    gepa_report_dir: Path
    gepa_display_progress: bool
    gepa_reflection_minibatch_size: int
    gepa_candidate_selection_strategy: str
    gepa_seed: int
    gepa_prefer_seed_on_tie: bool
    output_dir: Path
    artifacts_dir: Path
    prompts_seed_dir: Path
    prompts_optimized_dir: Path
    bypass_tool_consent: bool


def _require(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and set {name}."
        )
    return value.strip()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def normalize_gepa_lm(model_id: str) -> str:
    """Normalize a model id to a LiteLLM Ollama id (`ollama/<name>`).

    Accepts either ``llama3.1`` / ``granite4:3b`` or an already-prefixed
    ``ollama/llama3.1`` value. Other provider prefixes (e.g. ``openai/``) are left as-is.
    """
    mid = model_id.strip()
    if not mid:
        raise ValueError("GEPA model id must be non-empty")
    if "/" in mid:
        return mid
    return f"ollama/{mid}"


def load_settings(env_file: Path | None = None) -> Settings:
    """Load .env from project root (or given path) and return Settings."""
    dotenv_path = env_file or (PROJECT_ROOT / ".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)
    else:
        # Still allow env vars set in the shell; also try example defaults via getenv
        load_dotenv(PROJECT_ROOT / ".env.example", override=False)

    bypass = _as_bool(_require("BYPASS_TOOL_CONSENT", "true"))
    if bypass:
        os.environ["BYPASS_TOOL_CONSENT"] = "true"

    return Settings(
        ollama_host=_require("OLLAMA_HOST", "http://localhost:11434"),
        orchestrator_model=_require("OLLAMA_ORCHESTRATOR_MODEL", "llama3.1"),
        worker_model=_require("OLLAMA_WORKER_MODEL", "llama3.1"),
        gepa_task_lm=normalize_gepa_lm(_require("GEPA_TASK_LM", "ollama/llama3.1")),
        gepa_reflection_lm=normalize_gepa_lm(
            _require("GEPA_REFLECTION_LM", "ollama/llama3.1")
        ),
        gepa_max_metric_calls=int(_require("GEPA_MAX_METRIC_CALLS", "20")),
        gepa_data_dir=_as_path(_require("GEPA_DATA_DIR", "data/gepa")),
        gepa_runs_dir=_as_path(_require("GEPA_RUNS_DIR", "gepa_runs")),
        gepa_report_dir=_as_path(_require("GEPA_REPORT_DIR", "artifacts/gepa")),
        gepa_display_progress=_as_bool(_require("GEPA_DISPLAY_PROGRESS", "true")),
        gepa_reflection_minibatch_size=int(
            _require("GEPA_REFLECTION_MINIBATCH_SIZE", "3")
        ),
        gepa_candidate_selection_strategy=_require(
            "GEPA_CANDIDATE_SELECTION_STRATEGY", "pareto"
        ),
        gepa_seed=int(_require("GEPA_SEED", "0")),
        gepa_prefer_seed_on_tie=_as_bool(
            _require("GEPA_PREFER_SEED_ON_TIE", "true")
        ),
        output_dir=_as_path(_require("OUTPUT_DIR", "output/spa")),
        artifacts_dir=_as_path(_require("ARTIFACTS_DIR", "artifacts")),
        prompts_seed_dir=Path(__file__).resolve().parent / "prompts" / "seed",
        prompts_optimized_dir=Path(__file__).resolve().parent / "prompts" / "optimized",
        bypass_tool_consent=bypass,
    )


def with_gepa_models(
    settings: Settings,
    *,
    task_lm: str | None = None,
    reflection_lm: str | None = None,
) -> Settings:
    """Return a copy of settings with optional GEPA model overrides."""
    return Settings(
        ollama_host=settings.ollama_host,
        orchestrator_model=settings.orchestrator_model,
        worker_model=settings.worker_model,
        gepa_task_lm=normalize_gepa_lm(task_lm)
        if task_lm
        else settings.gepa_task_lm,
        gepa_reflection_lm=normalize_gepa_lm(reflection_lm)
        if reflection_lm
        else settings.gepa_reflection_lm,
        gepa_max_metric_calls=settings.gepa_max_metric_calls,
        gepa_data_dir=settings.gepa_data_dir,
        gepa_runs_dir=settings.gepa_runs_dir,
        gepa_report_dir=settings.gepa_report_dir,
        gepa_display_progress=settings.gepa_display_progress,
        gepa_reflection_minibatch_size=settings.gepa_reflection_minibatch_size,
        gepa_candidate_selection_strategy=settings.gepa_candidate_selection_strategy,
        gepa_seed=settings.gepa_seed,
        gepa_prefer_seed_on_tie=settings.gepa_prefer_seed_on_tie,
        output_dir=settings.output_dir,
        artifacts_dir=settings.artifacts_dir,
        prompts_seed_dir=settings.prompts_seed_dir,
        prompts_optimized_dir=settings.prompts_optimized_dir,
        bypass_tool_consent=settings.bypass_tool_consent,
    )
