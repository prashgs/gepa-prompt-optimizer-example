"""Ollama model factory for Strands agents."""

from __future__ import annotations

from strands.models.ollama import OllamaModel

from sdlc_agents.config import Settings


def make_ollama_model(settings: Settings, *, for_orchestrator: bool = False) -> OllamaModel:
    """Create an OllamaModel for the orchestrator or a worker."""
    model_id = (
        settings.orchestrator_model if for_orchestrator else settings.worker_model
    )
    return OllamaModel(host=settings.ollama_host, model_id=model_id)
