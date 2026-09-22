"""Artifact and SPA file helpers."""

from __future__ import annotations

from pathlib import Path

from sdlc_agents.config import Settings

PRD = "prd.md"
DESIGN = "design.md"
TEST_REPORT = "test_report.md"
REVIEW = "review.md"
INDEX_HTML = "index.html"
STYLES_CSS = "styles.css"
APP_JS = "app.js"


def ensure_dirs(settings: Settings) -> None:
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.prompts_optimized_dir.mkdir(parents=True, exist_ok=True)


def artifact_path(settings: Settings, name: str) -> Path:
    return settings.artifacts_dir / name


def spa_path(settings: Settings, name: str) -> Path:
    return settings.output_dir / name


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_artifact(settings: Settings, name: str, content: str) -> Path:
    return write_text(artifact_path(settings, name), content)


def read_artifact(settings: Settings, name: str) -> str:
    return read_text(artifact_path(settings, name))


def write_spa_file(settings: Settings, name: str, content: str) -> Path:
    return write_text(spa_path(settings, name), content)


def read_spa_file(settings: Settings, name: str) -> str:
    return read_text(spa_path(settings, name))


def load_prompt(settings: Settings, role: str) -> str:
    """Load optimized prompt if present, otherwise seed prompt."""
    optimized = settings.prompts_optimized_dir / f"{role}.txt"
    seed = settings.prompts_seed_dir / f"{role}.txt"
    if optimized.exists() and optimized.stat().st_size > 0:
        return optimized.read_text(encoding="utf-8").strip()
    if not seed.exists():
        raise FileNotFoundError(f"Missing seed prompt for role '{role}': {seed}")
    return seed.read_text(encoding="utf-8").strip()
