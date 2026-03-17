---
applyTo: "Dockerfile*,docker-compose*,compose*,.env*,scripts/**"
---

# Infrastructure & Config — canonical patterns

> These rules apply to Dockerfiles, Compose files, env files, and scripts.
> They complement the cross-cutting rules in `.github/copilot-instructions.md`.

## Python base image

Always `python:3.12-slim`. The project mandates Python 3.12.
`python:3.13` is **not** permitted — `Dockerfile.agent` currently violates this.

```dockerfile
# ✅
FROM python:3.12-slim

# ❌
FROM python:3.13-slim
```

## uv installation — pinned binary copy

Copy the pre-built `uv` binary from the official image at a **pinned version**.
Do not `pip install uv` (unpinned, slow).

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /usr/local/bin/
```

## Layer caching — dependency-first copy

Always copy lock files before source code so Docker can cache the dependency
layer across source-only changes.

```dockerfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
```

## Environment files

| File                   | Purpose                                                   | Gitignored?                  |
| ---------------------- | --------------------------------------------------------- | ---------------------------- |
| `.env`                 | Shared infra secrets (OpenAI, LangSmith, Postgres, Redis) | **Yes**                      |
| `.env.fastapi`         | API-specific settings (JWT secret, feature flags)         | **Yes**                      |
| `.env.agent`           | Agent-specific settings (Ollama URL, model names)         | **Yes** (create if missing)  |
| `.env.example`         | Template for `.env`                                       | No — committed               |
| `.env.fastapi.example` | Template for `.env.fastapi`                               | No — committed               |
| `.env.agent.example`   | Template for `.env.agent`                                 | No — committed               |
| `.env.dev`             | Dev defaults                                              | **Yes** — must be gitignored |

When adding a new environment variable, update **both** the `.env.*` file and
the corresponding `.env.*.example` template.

## No hardcoded credentials

Connection strings and secrets must come from environment variables. Never
use a fallback that contains literal credentials.

```python
# ✅ — fail fast if not configured
DATABASE_URL: str  # Pydantic Settings — raises on startup if missing

# ❌ — masks misconfiguration
os.getenv("DATABASE_URL", "postgresql+psycopg://user:password@db:5432/otis")
```

## Health checks

Every service in Compose must have a `healthcheck`. Use `pg_isready` for
Postgres, `redis-cli ping` for Redis, and an HTTP probe for the API.

```yaml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "user", "-d", "otis"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## Scripts (`scripts/`)

- Use `logging` — not `print()` — even in one-off scripts
- Connection strings must come from env vars or `.env` files, not be hardcoded
- Parameterize all SQL — no f-string interpolation into `text()`

## On-touch cleanup checklist

When you edit **any** infrastructure file, also fix these:

- [ ] `Dockerfile.agent`: change `FROM python:3.13-slim` → `FROM python:3.12-slim`;
      replace `pip install uv` → pinned `COPY --from=ghcr.io/astral-sh/uv:0.10.7`
- [ ] `.gitignore`: add `.env.dev` if not already listed
- [ ] `src/services/retrieval_service.py` (when touched): replace
      `"postgresql+psycopg://user:password@db:5432/otis"` default → raise on
      missing config (move to `Settings`)
- [ ] `src/services/embedding_service.py` (when touched): remove hardcoded
      `user:password` connection string at L42/L50
- [ ] `scripts/backfill_file_hashes.py` (when touched): replace `print()`
      with `logging`, replace hardcoded connection string with env var
- [ ] Add health checks to any Compose service that lacks them
      (currently missing: `api`, `worker`, `pgadmin`, `ollama`)
