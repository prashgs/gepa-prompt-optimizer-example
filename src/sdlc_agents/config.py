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
    output_dir: Path
    artifacts_dir: Path
    prompts_seed_dir: Path
    prompts_optimized_dir: Path
    gepa_data_dir: Path
    bypass_tool_consent: bool


def _require(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and set {name}."
        )
    return value.strip()


def load_settings(env_file: Path | None = None) -> Settings:
    """Load .env from project root (or given path) and return Settings."""
    dotenv_path = env_file or (PROJECT_ROOT / ".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)
    else:
        # Still allow env vars set in the shell; also try example defaults via getenv
        load_dotenv(PROJECT_ROOT / ".env.example", override=False)

    output_dir = Path(_require("OUTPUT_DIR", "output/spa"))
    artifacts_dir = Path(_require("ARTIFACTS_DIR", "artifacts"))
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    if not artifacts_dir.is_absolute():
        artifacts_dir = PROJECT_ROOT / artifacts_dir

    bypass = _require("BYPASS_TOOL_CONSENT", "true").lower() in {"1", "true", "yes"}
    if bypass:
        os.environ["BYPASS_TOOL_CONSENT"] = "true"

    return Settings(
        ollama_host=_require("OLLAMA_HOST", "http://localhost:11434"),
        orchestrator_model=_require("OLLAMA_ORCHESTRATOR_MODEL", "llama3.1"),
        worker_model=_require("OLLAMA_WORKER_MODEL", "llama3.1"),
        gepa_task_lm=_require("GEPA_TASK_LM", "ollama/llama3.1"),
        gepa_reflection_lm=_require("GEPA_REFLECTION_LM", "ollama/llama3.1"),
        gepa_max_metric_calls=int(_require("GEPA_MAX_METRIC_CALLS", "20")),
        output_dir=output_dir,
        artifacts_dir=artifacts_dir,
        prompts_seed_dir=Path(__file__).resolve().parent / "prompts" / "seed",
        prompts_optimized_dir=Path(__file__).resolve().parent / "prompts" / "optimized",
        gepa_data_dir=PROJECT_ROOT / "data" / "gepa",
        bypass_tool_consent=bypass,
    )
