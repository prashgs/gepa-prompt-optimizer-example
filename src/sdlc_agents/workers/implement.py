"""Implement worker agent."""

from __future__ import annotations

from strands import Agent

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings
from sdlc_agents.llm import make_ollama_model
from sdlc_agents.tools import make_file_tools


def build_implement_agent(settings: Settings) -> Agent:
    tools = make_file_tools(settings)
    return Agent(
        model=make_ollama_model(settings),
        system_prompt=art.load_prompt(settings, "implement"),
        tools=[
            tools["write_spa_file"],
            tools["read_spa_file"],
            tools["list_spa_files"],
            tools["read_artifact_file"],
        ],
    )


def run_implement(
    settings: Settings,
    brief: str,
    feedback: str | None = None,
    prd: str | None = None,
    design: str | None = None,
) -> str:
    agent = build_implement_agent(settings)
    prd_text = prd if prd is not None else art.read_artifact(settings, art.PRD)
    design_text = design if design is not None else art.read_artifact(settings, art.DESIGN)
    feedback_block = f"\n\nTest feedback to address:\n{feedback}\n" if feedback else ""
    prompt = (
        f"User brief:\n{brief}\n\n"
        f"PRD:\n{prd_text}\n\n"
        f"Design:\n{design_text}\n"
        f"{feedback_block}\n"
        "Implement the SPA. Write complete files with write_spa_file "
        f"(prefer '{art.INDEX_HTML}', '{art.STYLES_CSS}', '{art.APP_JS}'). "
        "Return a short confirmation listing files written."
    )
    result = agent(prompt)
    text = str(result)
    # Fallback: if no SPA files were written, persist a single-file HTML from the reply
    spa_files = list(settings.output_dir.glob("*")) if settings.output_dir.exists() else []
    spa_files = [p for p in spa_files if p.is_file() and p.name != ".gitkeep"]
    if not spa_files and "<html" in text.lower():
        art.write_spa_file(settings, art.INDEX_HTML, text)
    return text
