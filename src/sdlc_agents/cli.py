"""CLI entrypoints: run SDLC workflow and optimize prompts with GEPA."""

from __future__ import annotations

import argparse
import sys

from sdlc_agents.config import load_settings, with_gepa_models
from sdlc_agents.orchestrator import run_workflow
from sdlc_agents.roles import optimizable_role_ids


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

    settings = with_gepa_models(
        load_settings(),
        task_lm=args.task_lm,
        reflection_lm=args.reflection_lm,
    )
    roles = args.roles or None
    print("Optimizing prompts via GEPA ...")
    print(f"  task_lm (evaluated):     {settings.gepa_task_lm}")
    print(f"  reflection_lm (proposer): {settings.gepa_reflection_lm}")
    print(f"  max_metric_calls:        {settings.gepa_max_metric_calls}")
    print(f"  reflection_minibatch:    {settings.gepa_reflection_minibatch_size}")
    print(f"  candidate_strategy:      {settings.gepa_candidate_selection_strategy}")
    print(f"  seed:                    {settings.gepa_seed}")
    print(f"  report_dir:              {settings.gepa_report_dir}")
    written = optimize_all_prompts(settings, roles=roles)
    for path in written:
        print(f"Wrote prompt: {path}")
    report = settings.gepa_report_dir / "optimization_report.md"
    if report.exists():
        print(f"Wrote report: {report}")
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
        choices=list(optimizable_role_ids()),
        help=(
            "Subset of roles to optimize (default: all with optimize=true in "
            "config/roles.toml)"
        ),
    )
    opt_p.add_argument(
        "--task-lm",
        default=None,
        metavar="MODEL",
        help=(
            "LiteLLM / Ollama model used as GEPA task_lm (prompts are optimized for this model). "
            "Overrides GEPA_TASK_LM. Example: granite4:3b or ollama/granite4:3b"
        ),
    )
    opt_p.add_argument(
        "--reflection-lm",
        default=None,
        metavar="MODEL",
        help=(
            "LiteLLM / Ollama model used as GEPA reflection_lm (proposes better prompts). "
            "Prefer a stronger model than --task-lm. Overrides GEPA_REFLECTION_LM. "
            "Example: nemotron-mini:4b or ollama/nemotron-mini:4b"
        ),
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
