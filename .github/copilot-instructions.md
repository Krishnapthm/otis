# otis — cross-cutting rules

> Domain-specific rules live in `.github/instructions/` and are injected automatically
> when Copilot touches files matching their `applyTo` glob. This file covers only
> rules that apply to **every** file in the repo.

## Actual monorepo layout

```
src/api/        → FastAPI app      (entry: src/api/v1/main.py)
src/agents/     → LangGraph agent  (entry: src/agents/chat_agent.py)
src/services/   → shared business logic (no HTTP, no DB sessions)
src/core/       → config, security, hashing
src/tasks/      → RQ background workers
src/workers/    → worker entry points
frontend/otis-ui/ → Vite + React
migrations/     → raw SQL migrations
Dockerfile.*    → per-service images (repo root)
docker-compose.yml / compose.local.yml → orchestration (repo root)
```

## Non-negotiables (every file)

- **Python 3.12**, dependency management via `uv`
- **TypeScript strict mode**, zero `any`
- All services communicate via **typed interfaces** — never raw dicts/strings across boundaries
- **No hardcoded secrets** — env config via `.env` files and Pydantic `BaseSettings` only
- **Every public function/class needs a docstring or JSDoc comment**
  - Python: Google-style (see `src/core/hashing.py` as exemplar)
  - TypeScript: `/** */` JSDoc on all exported symbols

## DRY & separation of concerns

- Extract shared logic into `utils/` or `helpers/` modules — never duplicate across files
- Each module has a single responsibility: routers validate + dispatch, services contain logic, utils contain pure helpers
- **Dependency injection over singletons**: pass dependencies (DB sessions, LLM instances, config) as parameters or via FastAPI `Depends()` — never instantiate inline inside business logic

## Naming

- Python: `snake_case` for everything, `PascalCase` for classes, `SCREAMING_SNAKE` for module-level constants
- TypeScript: `camelCase` for variables/functions, `PascalCase` for components/types
- API routes: `kebab-case` (`/run-agent`, not `/runAgent`)
- No abbreviations in public names unless universally known (`llm`, `mcq`, `db` are acceptable)

## What NOT to generate

- No `print()` debugging — use `logging.getLogger(__name__)` in Python
- No `console.log` / `console.warn` / `console.debug` in committed TypeScript — `console.error()` in catch blocks only
- No inline SQL with f-string interpolation — use parameterized queries
- No raw HTTP strings — use defined API clients/services
- No new dependency without a comment in `pyproject.toml` or `package.json` explaining why

## Incremental cleanup rule

When touching **any** file, fix adjacent issues in that same file:
remove dead imports, add missing docstrings, replace `print()` with logger calls,
replace `any` with `unknown`, consolidate duplicated logic into utils.
Never leave a file worse than you found it. No separate refactor PRs needed.
