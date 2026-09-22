"""Design worker agent."""

from __future__ import annotations

from strands import Agent

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings
from sdlc_agents.llm import make_ollama_model
from sdlc_agents.tools import make_file_tools


def build_design_agent(settings: Settings) -> Agent:
    tools = make_file_tools(settings)
    return Agent(
        model=make_ollama_model(settings),
        system_prompt=art.load_prompt(settings, "design"),
        tools=[tools["write_artifact_file"], tools["read_artifact_file"]],
    )


def run_design(settings: Settings, brief: str, prd: str | None = None) -> str:
    agent = build_design_agent(settings)
    prd_text = prd if prd is not None else art.read_artifact(settings, art.PRD)
    prompt = (
        f"User brief:\n{brief}\n\n"
        f"PRD:\n{prd_text}\n\n"
        f"Write a Design document and save it using write_artifact_file "
        f"with filename '{art.DESIGN}'. Return a short confirmation."
    )
    result = agent(prompt)
    text = str(result)
    if not art.read_artifact(settings, art.DESIGN).strip() and text.strip():
        art.write_artifact(settings, art.DESIGN, text)
    return text
