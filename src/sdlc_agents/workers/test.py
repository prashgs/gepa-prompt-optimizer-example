"""Test worker agent."""

from __future__ import annotations

from strands import Agent

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings
from sdlc_agents.llm import make_ollama_model
from sdlc_agents.tools import make_file_tools


def build_test_agent(settings: Settings) -> Agent:
    tools = make_file_tools(settings)
    return Agent(
        model=make_ollama_model(settings),
        system_prompt=art.load_prompt(settings, "test"),
        tools=[
            tools["write_artifact_file"],
            tools["read_artifact_file"],
            tools["read_spa_file"],
            tools["list_spa_files"],
        ],
    )


def _gather_spa_sources(settings: Settings) -> str:
    parts: list[str] = []
    for name in (art.INDEX_HTML, art.STYLES_CSS, art.APP_JS):
        content = art.read_spa_file(settings, name)
        if content:
            parts.append(f"=== {name} ===\n{content}")
    if not parts and settings.output_dir.exists():
        for path in sorted(settings.output_dir.iterdir()):
            if path.is_file() and path.suffix in {".html", ".css", ".js"}:
                parts.append(f"=== {path.name} ===\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts) if parts else "(no SPA files found)"


def run_test(settings: Settings, brief: str, prd: str | None = None) -> str:
    agent = build_test_agent(settings)
    prd_text = prd if prd is not None else art.read_artifact(settings, art.PRD)
    spa = _gather_spa_sources(settings)
    prompt = (
        f"User brief:\n{brief}\n\n"
        f"PRD:\n{prd_text}\n\n"
        f"SPA source:\n{spa}\n\n"
        f"Write a test report and save it using write_artifact_file "
        f"with filename '{art.TEST_REPORT}'. "
        "Clearly state Overall verdict: PASS or FAIL. Return a short summary."
    )
    result = agent(prompt)
    text = str(result)
    if not art.read_artifact(settings, art.TEST_REPORT).strip() and text.strip():
        art.write_artifact(settings, art.TEST_REPORT, text)
    return text
