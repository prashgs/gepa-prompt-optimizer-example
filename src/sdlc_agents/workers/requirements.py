"""Requirements worker agent."""

from __future__ import annotations

from strands import Agent

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings
from sdlc_agents.llm import make_ollama_model
from sdlc_agents.tools import make_file_tools


def build_requirements_agent(settings: Settings) -> Agent:
    tools = make_file_tools(settings)
    return Agent(
        model=make_ollama_model(settings),
        system_prompt=art.load_prompt(settings, "requirements"),
        tools=[tools["write_artifact_file"], tools["read_artifact_file"]],
    )


def run_requirements(settings: Settings, brief: str) -> str:
    agent = build_requirements_agent(settings)
    prompt = (
        f"User brief:\n{brief}\n\n"
        f"Write a complete PRD in Markdown, then save the FULL PRD text using "
        f"write_artifact_file with filename '{art.PRD}'. "
        "After saving, return a short confirmation."
    )
    result = agent(prompt)
    text = str(result)
    # Ensure artifact exists even if the model forgot the write tool
    if not art.read_artifact(settings, art.PRD).strip() and text.strip():
        art.write_artifact(settings, art.PRD, text)
    return text
