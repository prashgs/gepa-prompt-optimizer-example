#!/usr/bin/env python3
"""Offline GEPA prompt optimization."""

from sdlc_agents.cli import main

if __name__ == "__main__":
    import sys

    main(["optimize", *sys.argv[1:]])
