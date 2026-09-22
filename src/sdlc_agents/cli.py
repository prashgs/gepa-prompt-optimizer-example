"""CLI entrypoints: run SDLC workflow and optimize prompts with GEPA."""

from __future__ import annotations

import argparse
import sys

from sdlc_agents.config import load_settings
from sdlc_agents.orchestrator import run_workflow


def cmd_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    brief = " ".join(args.brief).strip()
    if not brief:
        print("Error: provide a non-empty product brief.", file=sys.stderr)
        return 2
    print(f"Running SDLC workflow with Ollama at {settings.ollama_host} ...")
    print(f"Orchestrator model: {settings.orchestrator_model}")
    print(f"Worker model: {settings.worker_model}")
    print()
    result = run_workflow(brief, settings)
    print(result)
    print()
    print(f"Artifacts: {settings.artifacts_dir}")
    print(f"SPA output: {settings.output_dir}")
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    from sdlc_agents.gepa_optimize import optimize_all_prompts

    settings = load_settings()
    roles = args.roles or None
    print(f"Optimizing prompts via GEPA (task={settings.gepa_task_lm}) ...")
    written = optimize_all_prompts(settings, roles=roles)
    for path in written:
        print(f"Wrote {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdlc-agents",
        description="SDLC Orchestrator–Worker with Strands, Ollama, and GEPA",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run the SDLC agent workflow for a product brief")
    run_p.add_argument(
        "brief",
        nargs="+",
        help="Product brief, e.g. Build a todo list with localStorage",
    )
    run_p.set_defaults(func=cmd_run)

    opt_p = sub.add_parser(
        "optimize",
        help="Offline GEPA optimization of worker system prompts",
    )
    opt_p.add_argument(
        "--roles",
        nargs="+",
        choices=[
            "requirements",
            "design",
            "implement",
            "test",
            "review",
            "orchestrator",
        ],
        help="Subset of roles to optimize (default: all workers + orchestrator)",
    )
    opt_p.set_defaults(func=cmd_optimize)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
