"""Review worker agent."""

from __future__ import annotations

from strands import Agent

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings
from sdlc_agents.llm import make_ollama_model
from sdlc_agents.tools import make_file_tools
from sdlc_agents.workers.test import _gather_spa_sources


def build_review_agent(settings: Settings) -> Agent:
    tools = make_file_tools(settings)
    return Agent(
        model=make_ollama_model(settings),
        system_prompt=art.load_prompt(settings, "review"),
        tools=[
            tools["write_artifact_file"],
            tools["read_artifact_file"],
            tools["read_spa_file"],
            tools["list_spa_files"],
        ],
    )


def run_review(settings: Settings, brief: str) -> str:
    agent = build_review_agent(settings)
    prd = art.read_artifact(settings, art.PRD)
    design = art.read_artifact(settings, art.DESIGN)
    test_report = art.read_artifact(settings, art.TEST_REPORT)
    spa = _gather_spa_sources(settings)
    prompt = (
        f"User brief:\n{brief}\n\n"
        f"PRD:\n{prd}\n\n"
        f"Design:\n{design}\n\n"
        f"Test report:\n{test_report}\n\n"
        f"SPA source:\n{spa}\n\n"
        f"Write a final review and save it using write_artifact_file "
        f"with filename '{art.REVIEW}'. Return a short summary."
    )
    result = agent(prompt)
    text = str(result)
    if not art.read_artifact(settings, art.REVIEW).strip() and text.strip():
        art.write_artifact(settings, art.REVIEW, text)
    return text
