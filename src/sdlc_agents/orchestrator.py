"""Strands orchestrator using Agents-as-Tools for SDLC workers."""

from __future__ import annotations

from strands import Agent, tool

from sdlc_agents import artifacts as art
from sdlc_agents.config import Settings, load_settings
from sdlc_agents.llm import make_ollama_model
from sdlc_agents.workers.design import run_design
from sdlc_agents.workers.implement import run_implement
from sdlc_agents.workers.requirements import run_requirements
from sdlc_agents.workers.review import run_review
from sdlc_agents.workers.test import run_test


def build_orchestrator(settings: Settings | None = None) -> Agent:
    """Build the SDLC orchestrator with worker tools bound to settings."""
    settings = settings or load_settings()
    art.ensure_dirs(settings)

    @tool
    def requirements_agent(brief: str) -> str:
        """Create a PRD from the user brief and save artifacts/prd.md.

        Args:
            brief: The original product brief from the user
        """
        return run_requirements(settings, brief)

    @tool
    def design_agent(brief: str, prd_summary: str = "") -> str:
        """Create a design document from the brief/PRD and save artifacts/design.md.

        Args:
            brief: The original product brief
            prd_summary: Optional PRD text or notes; worker also reads artifacts/prd.md
        """
        prd = prd_summary or None
        return run_design(settings, brief, prd=prd)

    @tool
    def implement_agent(brief: str, feedback: str = "") -> str:
        """Implement the vanilla HTML/CSS/JS SPA under the output directory.

        Args:
            brief: The original product brief
            feedback: Optional test failure feedback for a fix pass
        """
        return run_implement(settings, brief, feedback=feedback or None)

    @tool
    def test_agent(brief: str) -> str:
        """Run static acceptance checks and save artifacts/test_report.md.

        Args:
            brief: The original product brief
        """
        return run_test(settings, brief)

    @tool
    def review_agent(brief: str) -> str:
        """Produce a final review and save artifacts/review.md.

        Args:
            brief: The original product brief
        """
        return run_review(settings, brief)

    return Agent(
        model=make_ollama_model(settings, for_orchestrator=True),
        system_prompt=art.load_prompt(settings, "orchestrator"),
        tools=[
            requirements_agent,
            design_agent,
            implement_agent,
            test_agent,
            review_agent,
        ],
    )


def run_workflow(brief: str, settings: Settings | None = None) -> str:
    """Run the full SDLC orchestrator pipeline for a user brief."""
    settings = settings or load_settings()
    art.ensure_dirs(settings)
    orchestrator = build_orchestrator(settings)
    user_message = (
        f"Build a simple interactive single-page app for this brief:\n\n{brief}\n\n"
        "Follow the required worker tool sequence. "
        f"SPA files go under {settings.output_dir}. "
        f"Artifacts go under {settings.artifacts_dir}."
    )
    result = orchestrator(user_message)
    return str(result)
