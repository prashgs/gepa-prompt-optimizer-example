# gepa-prompt-optimizer-example

SDLC **Orchestrator–Worker** agents that turn a product brief into a simple interactive vanilla HTML/CSS/JS SPA.

Stack:
- **AWS Strands Agents** — orchestrator + workers (Agents-as-Tools)
- **Ollama** — local LLMs
- **GEPA** — offline system-prompt optimization

## Prerequisites

1. [uv](https://docs.astral.sh/uv/) (installs and manages Python + dependencies)
2. [Ollama](https://ollama.com/) installed and running
3. Pull a tool-capable model, then set the same id in `.env`:

```bash
ollama serve
ollama pull llama3.1   # or granite4:3b, qwen2.5-coder, etc.
ollama list            # copy the model name into .env
```

Install uv if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

```bash
cd gepa-prompt-optimizer-example

# Create the virtualenv and install the project (reads pyproject.toml / uv.lock)
uv sync

# Runtime-only (skip the default dev group / pytest):
# uv sync --no-dev

cp .env.example .env
# Edit .env if your Ollama host or model names differ
```

## Optimize prompts (offline GEPA)

GEPA improves each worker (and orchestrator) system prompt against small local datasets, using Ollama via LiteLLM (`GEPA_TASK_LM` / `GEPA_REFLECTION_LM`).

```bash
# All roles (budget controlled by GEPA_MAX_METRIC_CALLS)
uv run sdlc-agents optimize
# or
uv run python -m sdlc_agents.cli optimize

# Or a subset
uv run sdlc-agents optimize --roles requirements implement

# Equivalent script
uv run python scripts/optimize_prompts.py
```

Optimized prompts are written to `src/sdlc_agents/prompts/optimized/<role>.txt`.  
At runtime, agents load **optimized** prompts when present, otherwise **seed** prompts.

## Run the SDLC workflow

```bash
uv run sdlc-agents run "Build a todo list with add, complete, delete, and localStorage"

# Or
uv run python scripts/run_workflow.py "Build a tip calculator SPA"
```

Pipeline (orchestrator may retry Implement once if Test fails):

1. **Requirements** → `artifacts/prd.md`
2. **Design** → `artifacts/design.md`
3. **Implement** → `output/spa/` (`index.html`, `styles.css`, `app.js`)
4. **Test** → `artifacts/test_report.md`
5. **Review** → `artifacts/review.md`

Open the SPA:

```bash
xdg-open output/spa/index.html   # or open in any browser
```

## Environment variables

See [`.env.example`](.env.example):

| Variable | Purpose |
|----------|---------|
| `OLLAMA_HOST` | Ollama base URL |
| `OLLAMA_ORCHESTRATOR_MODEL` | Model id for orchestrator |
| `OLLAMA_WORKER_MODEL` | Model id for workers |
| `GEPA_TASK_LM` | LiteLLM id, e.g. `ollama/llama3.1` |
| `GEPA_REFLECTION_LM` | LiteLLM id for GEPA reflection |
| `GEPA_MAX_METRIC_CALLS` | GEPA budget (keep small for local demos) |
| `OUTPUT_DIR` / `ARTIFACTS_DIR` | Output paths |
| `BYPASS_TOOL_CONSENT` | Non-interactive Strands tool use |

## Project layout

```
src/sdlc_agents/     # package: config, orchestrator, workers, GEPA
data/gepa/           # tiny train sets for prompt optimization
scripts/             # thin CLI wrappers
artifacts/           # generated PRD / design / tests / review
output/spa/          # generated SPA
uv.lock              # locked dependency versions (uv)
```

## Dependency management (uv)

```bash
uv sync                          # install from lockfile
uv add <package>                 # add a runtime dependency
uv add --group dev <package>     # add a dev dependency
uv lock                          # refresh uv.lock after editing pyproject.toml
uv run <command>                 # run inside the project environment
```
