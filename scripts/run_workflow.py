#!/usr/bin/env python3
"""Run the SDLC orchestrator workflow."""

from sdlc_agents.cli import main

if __name__ == "__main__":
    main(["run", *(__import__("sys").argv[1:])])
