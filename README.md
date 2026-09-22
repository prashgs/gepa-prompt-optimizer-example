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

GEPA improves each worker (and orchestrator) system prompt against small local datasets via LiteLLM.

Use **two different models** when you can:
- **`GEPA_TASK_LM` / `--task-lm`** — model the prompts are optimized *for* (ideally same family as your SDLC worker)
- **`GEPA_REFLECTION_LM` / `--reflection-lm`** — stronger proposer that rewrites prompts (can differ from task and from runtime agents)

```bash
# Defaults from .env (GEPA_TASK_LM / GEPA_REFLECTION_LM)
uv run sdlc-agents optimize

# Override models on the CLI (bare Ollama names or ollama/<name>)
uv run sdlc-agents optimize \
  --task-lm granite4:3b \
  --reflection-lm nemotron-mini:4b

# Subset of roles
uv run sdlc-agents optimize --roles requirements implement \
  --task-lm ollama/granite4:3b \
  --reflection-lm ollama/nemotron-mini:4b

# Equivalent script (pass the same flags after the script name)
uv run python scripts/optimize_prompts.py --task-lm granite4:3b --reflection-lm nemotron-mini:4b
```

Optimized prompts are written to `src/sdlc_agents/prompts/optimized/<role>.txt`.  
At runtime, agents load **optimized** prompts when present, otherwise **seed** prompts.

Each optimize run also writes Markdown reports under `GEPA_REPORT_DIR` (default `artifacts/gepa/`):

- `optimization_report.md` — combined report for the run
- `<role>.md` — per-role detail: **input** (seed + train examples), **reflections** (reflection LM prompts/outputs and proposals), and **final selected prompt**

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
| `GEPA_TASK_LM` | Model prompts are optimized for (`ollama/<name>` or bare Ollama name) |
| `GEPA_REFLECTION_LM` | Stronger model that proposes prompt rewrites |
| `GEPA_MAX_METRIC_CALLS` | GEPA evaluation budget |
| `GEPA_REFLECTION_MINIBATCH_SIZE` | Examples per reflection proposal |
| `GEPA_CANDIDATE_SELECTION_STRATEGY` | e.g. `pareto`, `current_best` |
| `GEPA_SEED` | RNG seed for GEPA |
| `GEPA_DISPLAY_PROGRESS` | Show GEPA progress bar (`true`/`false`) |
| `GEPA_PREFER_SEED_ON_TIE` | Keep seed when GEPA score does not improve |
| `GEPA_DATA_DIR` | Train/val JSON datasets directory |
| `GEPA_RUNS_DIR` | Per-role GEPA run state / logs |
| `GEPA_REPORT_DIR` | Markdown optimization reports |
| `OUTPUT_DIR` / `ARTIFACTS_DIR` | SPA and SDLC artifact paths |
| `BYPASS_TOOL_CONSENT` | Non-interactive Strands tool use |

## Project layout

```
config/roles.toml    # all SDLC roles (workers + orchestrator)
src/sdlc_agents/     # package: config, orchestrator, workers, GEPA
data/gepa/           # tiny train sets for prompt optimization
scripts/             # thin CLI wrappers
artifacts/           # generated PRD / design / tests / review / GEPA reports
output/spa/          # generated SPA
uv.lock              # locked dependency versions (uv)
```

Roles are defined in [`config/roles.toml`](config/roles.toml). Add or reorder entries there; the optimize CLI and GEPA defaults read from that file.

## Dependency management (uv)

```bash
uv sync                          # install from lockfile
uv add <package>                 # add a runtime dependency
uv add --group dev <package>     # add a dev dependency
uv lock                          # refresh uv.lock after editing pyproject.toml
uv run <command>                 # run inside the project environment
```
