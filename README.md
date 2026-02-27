# Otis

![Build](https://img.shields.io/badge/build-vite%20build-blue)
![License](https://img.shields.io/badge/license-UNLICENSED-lightgrey)
![Version](https://img.shields.io/badge/version-0.0.0-informational)

**TL;DR:** Otis ingests educational documents, extracts concepts, generates multiple-choice questions via a multi-node LangGraph agent, and provides a conversational AI tutor -- all behind a FastAPI backend with a React frontend. It is a prototype; expect rough edges, missing tests, and manual migration steps.

---

## Assumptions

Before reading, note the assumptions this document makes:

- You have basic familiarity with Python async frameworks, React/TypeScript, and Docker.
- You have access to an Azure OpenAI resource with `gpt-4o-mini` and `gpt-4.1-nano` deployments (or are willing to modify `src/agents/utils/llm_config.py`).
- You are running Linux or macOS. Windows users will need WSL2 for Docker volume mounts and Ollama.
- The Docker Compose setup is for **development only**. There is no production deployment configuration.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack Summary](#tech-stack-summary)
- [Monorepo Layout](#monorepo-layout)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Environment Variable Matrix](#environment-variable-matrix)
- [Quick Start (Docker)](#quick-start-docker)
- [Quick Start (Local Dev)](#quick-start-local-dev)
- [Local Dev (Frontend + Backend)](#local-dev-frontend--backend)
- [Deployment Coordination Checklist](#deployment-coordination-checklist)
- [Database Setup](#database-setup)
- [Running Tests](#running-tests)
- [LangGraph Agent Diagram](#langgraph-agent-diagram)

---

## Project Overview

Otis is an educational assessment and tutoring platform. The pipeline works as follows: an educator uploads a document (PDF); the system extracts text, splits it into chunks, and generates vector embeddings via a local Ollama instance; a concept extraction step identifies the key topics in the document; then, on demand, a LangGraph-based agent generates multiple-choice questions (MCQs) with stems, distractors, and explanations -- validated in a retry loop. The same agent handles conversational tutoring by routing user messages through scope and intent classifiers before responding with document-grounded answers. Target users are educators who want to generate assessments from their own material, and students who interact with the conversational tutor. The core value proposition is turning a static document into an interactive assessment and tutoring experience without manual question authoring.

---

## Tech Stack Summary

| Component           | Technology                               | Role                                                                  |
| ------------------- | ---------------------------------------- | --------------------------------------------------------------------- |
| API framework       | FastAPI 0.118+                           | Async REST API, SSE streaming                                         |
| Agent orchestration | LangGraph 0.6+                           | Stateful multi-node agent graphs with checkpointing                   |
| LLM inference       | Azure OpenAI (gpt-4o-mini, gpt-4.1-nano) | All LLM calls: classification, planning, generation, validation, chat |
| Embeddings          | Ollama (nomic-embed-text)                | Local embedding generation -- 768-dim vectors                         |
| Document parsing    | Docling 2.65, PyMuPDF                    | PDF-to-Markdown extraction                                            |
| Vector store        | Postgres 17 + pgvector                   | Chunk storage and similarity search                                   |
| Database ORM        | SQLAlchemy 2.0 (async) + asyncpg         | All DB access                                                         |
| Background jobs     | Redis 7 + RQ                             | Embedding tasks queued to a worker process                            |
| Config              | Pydantic Settings                        | Typed env var loading from `.env.fastapi`                             |
| Auth                | python-jose + passlib/bcrypt             | JWT access/refresh tokens                                             |
| Frontend framework  | React 19 + TypeScript 5.9                | SPA                                                                   |
| Build tool          | Vite (rolldown-vite 7.2)                 | Dev server and production build                                       |
| Styling             | Tailwind CSS 4.1                         | Utility-first CSS                                                     |
| UI components       | shadcn/ui (Radix primitives)             | Accessible component library                                          |
| Data fetching       | TanStack Query 5                         | Server state management, caching                                      |
| DB admin            | pgAdmin 4                                | Web-based Postgres management (dev only)                              |

### Why Azure OpenAI + Ollama (hybrid)?

LLM inference uses Azure OpenAI because it provides access to high-quality models (gpt-4.1-nano for fast classification/validation, gpt-4o-mini for generation) with managed rate limits and SLAs. Embeddings use Ollama running locally (or in a container) with `nomic-embed-text` because embeddings are high-volume, latency-tolerant, and running them locally avoids per-token costs and keeps document content off external APIs. The trade-off: you must run an Ollama instance, which needs disk space for the model weights (~274 MB for nomic-embed-text).

---

## Monorepo Layout

### Generated repository tree (current snapshot)

```text
otis/
- CONTRIBUTING.md
- Dockerfile.agent
- Dockerfile.api
- README.md
- VECTORSTORE_REFACTOR_SUMMARY.md
- docker-compose.yml
- pyproject.toml
- main.py
- models.py
- prompts.py
- src/
    - agents/
        - nodes/
        - prompts/
        - utils/
    - api/
        - crud/
        - db/
        - routers/
        - utils/
        - v1/
    - core/
    - services/
    - tasks/
    - worker.py
- frontend/
    - otis-ui/
        - src/
        - public/
        - package.json
        - vite.config.ts
- docs/
    - ARCHITECTURE.md
    - BACKEND_REFERENCE.md
    - FRONTEND_REFERENCE.md
    - DATA_FLOW.md
    - API_CONTRACT.md
    - DOCUMENTATION_PLAN.md
    - ENVIRONMENT_VARIABLES.md
    - RETRIEVAL_FLOW.md
- migrations/
    - 001_vectorstore_refactor.sql
    - 002_document_concepts.sql
    - 003_chat_message_events.sql
    - add_dedup_lean.sql
- scripts/
    - README.md
    - backfill_file_hashes.py
- tests/
    - test_security_tokens.py
```

```text
otis/
+-- main.py                   # Legacy entry point (unused -- API starts via src.api.v1.main)
+-- models.py                 # Legacy models file (unused)
+-- prompts.py                # Legacy prompts file (unused)
+-- quiz.json                 # Legacy quiz fixture (unused)
+-- testagentserver.py        # Legacy test server (unused)
+-- pyproject.toml            # Python project config, all backend dependencies
+-- docker-compose.yml        # Orchestrates all services (db, redis, ollama, api, worker, pgadmin)
+-- Dockerfile.api            # API + worker container image (Python 3.12 + uv)
+-- Dockerfile.agent          # Separate agent image (unused in current docker-compose)
+-- .env.example              # Template: shared env vars (Azure creds, Postgres, pgAdmin)
+-- .env.fastapi.example      # Template: FastAPI-specific env vars (DB_URL, JWT, CORS)
|
+-- src/                      # ---- BACKEND ----
|   +-- api/                  # FastAPI routers, CRUD, DB models, middleware
|   |   +-- v1/main.py        # App factory, lifespan, CORS, router registration
|   |   +-- routers/          # auth, chat, docs, embeddings, mcqs, projects, agent
|   |   +-- crud/             # DB query functions
|   |   +-- db/               # SQLAlchemy models, session factory, schema
|   |   +-- utils/            # Helpers (pagination, file handling)
|   +-- agents/               # LangGraph agent definitions
|   |   +-- chat_agent.py     # Main chat graph builder (the primary graph)
|   |   +-- mcq_subgraph.py   # MCQ question generation subgraph (stem -> options -> validate)
|   |   +-- graph.py          # Older generation graph (SSE flow, still compiled at startup)
|   |   +-- nodes/            # Individual graph node implementations
|   |   +-- prompts/          # Prompt templates per node
|   |   +-- utils/            # LLM config, state definitions, helpers
|   +-- services/             # Business logic layer
|   |   +-- retrieval_service.py   # Two-layer concept-aware RAG retrieval
|   |   +-- embedding_service.py   # Document parsing, chunking, embedding
|   |   +-- concept_service.py     # Concept extraction from documents
|   |   +-- file_handling.py       # File upload processing
|   +-- core/                 # Cross-cutting: config, security, hashing
|   +-- tasks/                # RQ task definitions (embedding_tasks.py)
|   +-- worker.py             # RQ worker entry point
|   +-- file_handling.py      # Legacy file handler (see src/services/file_handling.py)
|   +-- graph.py              # Legacy graph (see src/agents/graph.py)
|   +-- mcq.py                # Legacy MCQ (see src/agents/mcq.py)
|
+-- frontend/otis-ui/         # ---- FRONTEND ----
|   +-- src/
|   |   +-- App.tsx           # Root component, routing
|   |   +-- api/              # API client functions, authApi
|   |   +-- app/              # App-level providers
|   |   +-- components/       # UI components (shadcn/ui based)
|   |   +-- hooks/            # Custom React hooks
|   |   +-- lib/              # Utility functions
|   |   +-- pages/            # Route-level page components
|   +-- package.json          # Frontend dependencies
|   +-- vite.config.ts        # Vite config with path aliases
|   +-- tsconfig.json         # TypeScript config
|
+-- migrations/               # ---- INFRASTRUCTURE ----
|   +-- 001_vectorstore_refactor.sql
|   +-- 002_document_concepts.sql
|   +-- 003_chat_message_events.sql
|   +-- add_dedup_lean.sql
|
+-- scripts/                  # One-off maintenance scripts
|   +-- backfill_file_hashes.py
|
+-- experiments/              # Notebook experiments (not part of production)
+-- docs/                     # Architecture documentation
+-- tests/                    # Backend tests (minimal)
+-- uploads/                  # User-uploaded files (gitignored, created at runtime)
+-- thumbnails/               # Generated thumbnails (gitignored, created at runtime)
+-- postgres_data/            # Docker volume mount for Postgres (gitignored)
```

### Why this layout?

There is no monorepo tool (Nx, Turborepo). Services are coordinated exclusively via `docker-compose.yml`. The Python backend lives at the repo root (not in a `backend/` subfolder) because it was the original project; the frontend was added later under `frontend/otis-ui/`. Files marked "Legacy/unused" above are artifacts from earlier iterations -- they are not imported by any active code path but have not been removed.

---

## Prerequisites

| Requirement                 | Version       | Verify with              |
| --------------------------- | ------------- | ------------------------ |
| Python                      | >=3.12, <3.13 | `python3 --version`      |
| uv (Python package manager) | >=0.10        | `uv --version`           |
| Node.js                     | >=18          | `node --version`         |
| npm                         | >=9           | `npm --version`          |
| Docker                      | >=24          | `docker --version`       |
| Docker Compose              | v2 (plugin)   | `docker compose version` |
| Ollama (local dev only)     | any recent    | `ollama --version`       |

If running via Docker Compose (recommended), you only need Docker and Docker Compose installed locally. Python/Node/Ollama are handled inside containers.

If running locally (without Docker for the API/frontend), you need all of the above. Ollama must be installed and running with the `nomic-embed-text` model pulled:

```bash
ollama pull nomic-embed-text
```

---

## Environment Variables

Otis uses two env files. The split exists because `docker-compose.yml` loads `.env` for infrastructure services (Postgres, pgAdmin, Ollama) and both `.env` + `.env.fastapi` for the API/worker containers. The FastAPI `Settings` class reads from `.env.fastapi` only (configured via `SettingsConfigDict.env_file`).

### `.env` -- Infrastructure and shared secrets

| Variable                   | Description                   | Required | Default                           | Read by                                         |
| -------------------------- | ----------------------------- | -------- | --------------------------------- | ----------------------------------------------- |
| `AZURE_OPENAI_ENDPOINT`    | Azure OpenAI resource URL     | Yes      | --                                | API (via `langchain_openai` env auto-detection) |
| `AZURE_OPENAI_API_KEY`     | Azure OpenAI API key          | Yes      | --                                | API (via `langchain_openai` env auto-detection) |
| `LANGSMITH_TRACING`        | Enable LangSmith trace export | No       | `true`                            | API, worker                                     |
| `LANGSMITH_ENDPOINT`       | LangSmith API endpoint        | No       | `https://api.smith.langchain.com` | API, worker                                     |
| `LANGSMITH_API_KEY`        | LangSmith API key             | No       | --                                | API, worker                                     |
| `LANGSMITH_PROJECT`        | LangSmith project name        | No       | --                                | API, worker                                     |
| `POSTGRES_USER`            | Postgres superuser name       | Yes      | --                                | db container, connection strings                |
| `POSTGRES_PASSWORD`        | Postgres superuser password   | Yes      | --                                | db container, connection strings                |
| `POSTGRES_DB`              | Postgres database name        | Yes      | --                                | db container, connection strings                |
| `PGADMIN_DEFAULT_EMAIL`    | pgAdmin login email           | No       | --                                | pgadmin container                               |
| `PGADMIN_DEFAULT_PASSWORD` | pgAdmin login password        | No       | --                                | pgadmin container                               |
| `VITE_API_BASE_URL`        | API base URL for frontend     | Yes      | --                                | Frontend build (compile-time)                   |

### `.env.fastapi` -- FastAPI application settings

| Variable                         | Description                                   | Required | Default                                             | Read by                 |
| -------------------------------- | --------------------------------------------- | -------- | --------------------------------------------------- | ----------------------- |
| `DB_URL`                         | Async Postgres connection string              | Yes      | --                                                  | API (Pydantic Settings) |
| `JWT_SECRET_KEY`                 | HMAC key for JWT signing (min 32 bytes hex)   | Yes      | --                                                  | API                     |
| `JWT_ALGORITHM`                  | JWT signing algorithm                         | No       | `HS256`                                             | API                     |
| `ACCESS_TOKEN_EXPIRE_MINUTES`    | Access token TTL                              | No       | `30`                                                | API                     |
| `REFRESH_TOKEN_EXPIRE_DAYS`      | Refresh token TTL                             | No       | `7`                                                 | API                     |
| `REDIS_URL`                      | Redis connection URL                          | No       | `redis://localhost:6379/0`                          | API, worker             |
| `CORS_ORIGINS`                   | JSON array of allowed origins                 | No       | `["http://localhost:3000","http://localhost:5173"]` | API                     |
| `UPLOADS_DIR`                    | Path to uploaded files directory              | No       | --                                                  | API                     |
| `NUM_SEARCH_QUERIES`             | Number of retrieval queries to generate       | No       | `5`                                                 | API                     |
| `MAX_RETRIEVED_CHUNKS`           | Cap on returned RAG chunks                    | No       | `20`                                                | API                     |
| `USE_NAIVE_MCQ_GENERATOR`        | Use legacy MCQ generator instead of agent     | No       | `false`                                             | API                     |
| `CHAT_GRAPH_RETRIEVAL_ENABLED`   | Enable document retrieval in chat             | No       | `true`                                              | API                     |
| `CHAT_ROUTER_RETRIEVAL_FALLBACK` | Fall back to retrieval when intent is unclear | No       | `false`                                             | API                     |

### Failure behavior

- Missing `DB_URL` or `JWT_SECRET_KEY`: the API will crash immediately on startup with a Pydantic `ValidationError`.
- Missing `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY`: the API starts, but any LLM call will fail with an authentication error at request time.
- Missing or unreachable `REDIS_URL`: the API starts, but background embedding jobs will fail to enqueue. The worker process will exit on startup.
- Wrong `OLLAMA_BASE_URL`: embedding calls will hang or timeout. The worker container sets this to `http://ollama:11434` via docker-compose; local dev should use `http://localhost:11434`.

### Setup from templates

```bash
cp .env.example .env
cp .env.fastapi.example .env.fastapi
```

Then fill in the values. At minimum you need: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_URL`, `JWT_SECRET_KEY`.

The `DB_URL` format for Docker:

```text
DB_URL=postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@db:5432/<POSTGRES_DB>
```

For local dev (Postgres on host):

```text
DB_URL=postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@localhost:5432/<POSTGRES_DB>
```

## Environment Variable Matrix

Canonical source: see [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for a single table covering each variable, which file it belongs in (`.env` vs `.env.fastapi`), and which service reads it.

---

## Quick Start (Docker)

This is the recommended path. It starts Postgres (with pgvector), Redis, Ollama, the FastAPI API, and the RQ worker -- all in containers.

```bash
# 1. Clone and enter the repo
git clone <repo-url> otis && cd otis

# 2. Create env files from templates
cp .env.example .env
cp .env.fastapi.example .env.fastapi
# Edit both files -- fill in Azure OpenAI creds, Postgres creds, JWT secret, DB_URL

# 3. Start all services
docker compose up --build -d

# 4. Wait for healthy status
docker compose ps
# db, redis should show "healthy"; api, worker, ollama should show "running"

# 5. Pull the embedding model into the Ollama container (first time only)
docker compose exec ollama ollama pull nomic-embed-text

# 6. Run database migrations (first time or after pulling new migration files)
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/001_vectorstore_refactor.sql
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/002_document_concepts.sql
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/003_chat_message_events.sql
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/add_dedup_lean.sql
```

### Access points

| Service            | URL                        |
| ------------------ | -------------------------- |
| API (FastAPI docs) | http://localhost:8000/docs |
| pgAdmin            | http://localhost:5050      |
| Ollama             | http://localhost:11434     |

The frontend is **not** included in `docker-compose.yml`. You must run it locally:

```bash
cd frontend/otis-ui
npm install
npm run dev
# Vite dev server at http://localhost:5173
```

Set `VITE_API_BASE_URL=http://localhost:8000` in your `.env` (or as a shell env var) so the frontend can reach the API.

### What `--reload` means

The API container command includes `--reload`:

```text
uv run uvicorn src.api.v1.main:app --host 0.0.0.0 --port 8000 --reload
```

This tells uvicorn to watch for file changes and restart automatically. The `./src` directory is mounted from the host into the container, so edits on the host immediately take effect. This is a **development convenience** and should not be used in production (it adds filesystem polling overhead and can restart mid-request).

### Common failures

- **`db` container exits:** Check `docker compose logs db`. Usually a permissions issue with `./postgres_data/` or a missing env var.
- **`api` container restart loop:** Check `docker compose logs api`. Usually a missing `DB_URL` or `JWT_SECRET_KEY`.
- **Embedding jobs silently fail:** Check `docker compose logs worker`. The worker needs Ollama to be reachable at `http://ollama:11434` and the model pulled.
- **Port conflict:** If 5432, 8000, 5050, 6379, or 11434 is already in use, either stop the conflicting process or change the port mapping in `docker-compose.yml`.

---

## Quick Start (Local Dev)

Run the API and frontend directly on your machine, without Docker for the application code. You still need Postgres, Redis, and Ollama running -- either via Docker or installed natively.

### 1. Infrastructure services

The simplest approach is running just the infrastructure via Docker:

```bash
# Start only db, redis, ollama, pgadmin
docker compose up db redis ollama pgadmin -d

# Pull the embedding model
ollama pull nomic-embed-text
# Or if Ollama is in Docker:
docker compose exec ollama ollama pull nomic-embed-text
```

### 2. Backend

```bash
# Install Python dependencies
uv sync

# Set env vars -- the Ollama URL must point to localhost, not the Docker service name
# In .env.fastapi, ensure:
#   DB_URL=postgresql+asyncpg://user:password@localhost:5432/otis
#   REDIS_URL=redis://localhost:6379/0

# Start the API
uv run uvicorn src.api.v1.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal, start the worker
OLLAMA_BASE_URL=http://localhost:11434 uv run python -m src.worker
```

**Critical:** The `OLLAMA_BASE_URL` defaults to `http://ollama:11434` (the Docker service name) in `src/agents/utils/llm_config.py`. When running locally, the worker and any code importing `llm_config.py` will fail to connect unless you either:

- Set `OLLAMA_BASE_URL=http://localhost:11434` as an environment variable, **or**
- Edit `llm_config.py` directly (not recommended -- it will break Docker).

Currently, `llm_config.py` hardcodes the base URL. This is a known gap.

### 3. Frontend

```bash
cd frontend/otis-ui
npm install
npm run dev
```

Vite dev server starts at http://localhost:5173. The API proxy is **not configured** in `vite.config.ts`, so you must set `VITE_API_BASE_URL=http://localhost:8000` for the frontend to reach the API. CORS on the API side allows `http://localhost:5173` by default.

## Local Dev (Frontend + Backend)

Use one of these two supported setups:

1. **Docker infra + local app processes**
   - Run `db`, `redis`, and `ollama` with Docker.
   - Run FastAPI + worker locally (`uv run ...`).
   - Run frontend locally (`npm run dev`).
2. **Mostly Docker + local frontend**
   - Run backend + worker in Docker Compose.
   - Run frontend locally on port 5173.

Coordination rules:

- Set `VITE_API_BASE_URL=http://localhost:8000` before starting the frontend.
- Keep API CORS origins aligned with frontend origin (`http://localhost:5173` in dev).
- Do not rely on Vite proxying for `/v1`; this repo uses explicit API base URLs.

## Deployment Coordination Checklist

When moving from localhost to a deployed domain, update both sides together:

- Frontend: set `VITE_API_BASE_URL` to the deployed API origin at build time.
- Backend: set `CORS_ORIGINS` to deployed frontend origin(s), removing localhost-only defaults.
- Agent client: replace hardcoded `http://localhost:8000` in `frontend/otis-ui/src/api/agentApi.ts` with env-based base URL logic.
- Verify SSE endpoints (`/v1/chats/*/invoke`, `/v1/graph/*`) through the target domain/reverse proxy.

---

## Database Setup

Otis uses Postgres 17 with the `pgvector` extension for vector similarity search. The Docker image `pgvector/pgvector:pg17` includes pgvector pre-installed.

### Migrations

There is no migration framework (no Alembic, no Flyway). Migrations are raw SQL files, applied manually in order. This was a deliberate trade-off for speed during prototyping -- the schema was changing rapidly and Alembic's migration chain added friction. The cost is that there is no `alembic upgrade head` equivalent; you must track which migrations have been applied yourself.

Apply in this order:

```bash
psql -U <user> -d <dbname> -f migrations/001_vectorstore_refactor.sql
psql -U <user> -d <dbname> -f migrations/002_document_concepts.sql
psql -U <user> -d <dbname> -f migrations/003_chat_message_events.sql
psql -U <user> -d <dbname> -f migrations/add_dedup_lean.sql
```

| Migration                      | What it does                                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `001_vectorstore_refactor.sql` | Adds `user_id`, `is_embedded`, `embedded_at` to documents; creates `user_vectorstores`; drops old embedding tables |
| `002_document_concepts.sql`    | Creates `document_concepts` table with `VECTOR(768)` column for concept embeddings                                 |
| `003_chat_message_events.sql`  | Creates `chat_message_events` table for persistent SSE event replay                                                |
| `add_dedup_lean.sql`           | Adds `file_hash`, `content_hash`, `status`, `canonical_document_id` to documents; enables pgcrypto                 |

### Failure behavior

- Running a migration twice: most statements use `IF NOT EXISTS` / `IF EXISTS` guards, but not all. Re-running `001` may fail on the `ALTER TABLE ... ADD COLUMN` if the column already exists without the guard. Check for errors and skip manually if needed.
- Running out of order: `002` depends on `documents` table existing (from `001`). `003` depends on `chat_messages` table (created by the initial schema, not in these migrations). Running out of order will produce foreign key errors.

### Backfill script

After applying `add_dedup_lean.sql`, existing documents have `file_hash = 'PENDING_BACKFILL'`. Run the backfill script to compute actual hashes:

```bash
# From the repo root
uv run python -m scripts.backfill_file_hashes
```

This streams documents in batches of 100, reads each file from the `uploads/` directory, and writes the SHA-256 hash back. If a file is missing from disk, the hash remains `PENDING_BACKFILL`.

### LangGraph checkpoint tables

On first startup, the API lifespan function calls `AsyncPostgresSaver.setup()`, which creates the LangGraph checkpoint tables (`checkpoints`, `checkpoint_writes`, etc.) automatically. No manual migration needed for these.

---

## Running Tests

Test coverage is minimal. This section documents what exists, not what should exist.

### Backend

One test file exists: `tests/test_security_tokens.py`. It tests JWT access/refresh token creation, decoding, and refresh token revocation.

```bash
uv run -m unittest tests/test_security_tokens.py
```

There is no test runner configured in `pyproject.toml` (no pytest config, no `[tool.pytest]` section). The test uses `unittest` directly.

### Frontend

One test file exists: `frontend/otis-ui/src/api/authApi.test.ts`. It tests the `resolveApiBaseUrl` helper (2 assertions).

```bash
cd frontend/otis-ui
npm run test
# Runs: vitest run
```

Vitest is configured as a dev dependency in `package.json` with the script `"test": "vitest run"`.

### What is not tested

- All agent graph logic (nodes, routing, state transitions)
- All API endpoints (auth, CRUD, chat, embeddings, MCQ generation)
- All services (retrieval, embedding, concept extraction)
- All frontend components, pages, hooks, and API client logic beyond `resolveApiBaseUrl`
- Database migrations (no rollback tests, no idempotency tests)

Building test infrastructure is a priority.

---

## LangGraph Agent Diagram

Otis has two LangGraph graphs: the **main chat graph** (handles all user interactions) and the **MCQ question subgraph** (generates and validates a single MCQ). The main graph fans out to the subgraph via LangGraph's `Send` API for parallel question generation.

### Main Chat Graph

```mermaid
flowchart TD
    START((START)) --> scope_classifier

    scope_classifier -->|ALLOW| intent_classifier
    scope_classifier -->|BLOCK| END_NODE((END))

    intent_classifier -->|"PLAN: mcq_request / followup"| planner
    intent_classifier -->|"TOOLS: utility_task"| chat_tools
    intent_classifier -->|"CHAT: clarification / other"| chat_model

    planner -->|"GENERATE: new MCQ set"| retrieval
    planner -->|"PATCH: edit existing"| chat_tools

    retrieval --> require_retrieved_chunks

    require_retrieved_chunks -->|HAVE_CHUNKS| dispatch_questions
    require_retrieved_chunks -->|NO_CHUNKS| chat_model

    dispatch_questions -->|"Send() x N fan-out"| question_subgraph_runner

    question_subgraph_runner --> assemble_final_output
    assemble_final_output --> finalize_metadata
    finalize_metadata --> chat_model

    chat_tools -->|"BUMP: artifact_bump=true"| finalize_metadata
    chat_tools -->|"CHAT: no artifact change"| chat_model

    chat_model --> END_NODE
```

#### Node descriptions

| Node                       | Implementation                                                    | Purpose                                                                                                                                   |
| -------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `scope_classifier`         | `nodes/scope.py` via `guardrail_llm` (gpt-4.1-nano)               | Blocks out-of-scope or harmful prompts. Returns `ALLOW` or `BLOCK`.                                                                       |
| `intent_classifier`        | `nodes/intent.py` via `intent_llm` (gpt-4.1-nano)                 | Classifies user intent: `mcq_request`, `followup`, `utility_task`, `clarification`.                                                       |
| `planner`                  | `nodes/planner.py` via `planner_llm` (gpt-4.1-nano)               | Produces a `TestGenerationPlan`: topic, difficulty, Bloom's level, num questions, retrieval queries, distractor strategy.                 |
| `retrieval`                | `nodes/retrieval.py`                                              | Calls the two-layer retrieval service (see below). Streams progress via `get_stream_writer()`.                                            |
| `require_retrieved_chunks` | Inline in `chat_agent.py`                                         | Gate: if retrieval returned zero chunks, routes to `chat_model` with an error message instead of proceeding to generation.                |
| `dispatch_questions`       | No-op node                                                        | Entry point for `Send()` fan-out. Returns empty dict.                                                                                     |
| `question_subgraph_runner` | Invokes MCQ subgraph                                              | Runs the subgraph for one question index. Returns `{"mcq_drafts": [draft]}`. Results are aggregated via `Annotated[List[MCQDraft], add]`. |
| `assemble_final_output`    | `nodes/output.py`                                                 | Converts raw `MCQDraft` list into `FinalMCQ` list with lettered options (A/B/C/D).                                                        |
| `finalize_metadata`        | `nodes/output.py`                                                 | Bumps `artifact_version`, computes `retrieval_signature`.                                                                                 |
| `chat_tools`               | `nodes/chat.py` via `chat_with_tools_node`                        | Handles utility tasks (e.g., patching existing MCQs). May set `artifact_bump=true`.                                                       |
| `chat_model`               | `nodes/chat.py` via `chat_no_tools_llm` (gpt-4.1-nano, streaming) | Final response generation. Streams tokens to the client.                                                                                  |

#### Routing logic

- **`route_scope`:** Reads `state.before_agent_guardrail.intent`. If not `"ALLOW"`, the graph ends immediately -- no response is generated.
- **`route_intent`:** Maps `state.intent.intent` to one of three branches. Both `mcq_request` and `followup` go to the planner. `utility_task` goes to tool use. Everything else is plain chat.
- **`route_after_planner`:** If `edit_mode=true` and `edit_strategy="patch"`, routes to `chat_tools` for surgical edits instead of full regeneration.
- **`question_fanout_router`:** Uses `Send()` to create N parallel subgraph invocations. In edit mode with targeted indices, only the specified question indices are regenerated.
- **`route_retrieval_gate`:** Checks `len(state.retrieved_chunks) > 0`. If zero, falls through to chat with an error message.
- **`route_after_tools`:** If `chat_tools` set `artifact_bump=true`, routes through `finalize_metadata` to update versioning before chat.

### MCQ Question Subgraph

```mermaid
flowchart TD
    START((START)) --> stem_generator
    stem_generator --> options_generator
    options_generator --> validator

    validator -->|PASS| finalize_draft
    validator -->|"RETRY: retry_count lt 2"| stem_generator
    validator -->|"FAIL: retry_count gte 2"| finalize_draft

    finalize_draft --> END_NODE((END))
```

#### Node descriptions

| Node                | Implementation                                          | Purpose                                                                                                     |
| ------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `stem_generator`    | `nodes/generation/` via `stem_llm` (gpt-4.1-nano)       | Generates the question stem from the plan and retrieved chunks.                                             |
| `options_generator` | `nodes/generation/` via `options_llm` (gpt-4.1-nano)    | Generates answer options (correct answer + distractors) for the stem.                                       |
| `validator`         | `nodes/validator.py` via `validator_llm` (gpt-4.1-nano) | Validates the question for quality, correctness, and alignment with the plan. Returns pass/fail + feedback. |
| `finalize_draft`    | Inline in `mcq_subgraph.py`                             | Packages results into an `MCQDraft` object. Runs on both PASS and FAIL (max retries exceeded).              |

#### Retry behavior

The subgraph retries up to `_SUBGRAPH_MAX_RETRIES = 2` times. On each retry, the full stem-options-validate loop runs again. After 2 failed validations, the draft is finalized as-is (with `validation_feedback` populated so the user can see why it did not pass). Total worst-case LLM calls per question: 3 attempts x 3 nodes = 9 calls.

### RAG Retrieval Strategy

The retrieval node calls `src/services/retrieval_service.py`, which implements a two-layer retrieval strategy:

| Parameter                 | Value                                                                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Embedding model           | `nomic-embed-text` (768 dimensions) via Ollama                                                                                                  |
| Chunk splitting           | `RecursiveCharacterTextSplitter`, chunk_size=800, chunk_overlap=100                                                                             |
| Document parsing          | Docling (PDF pipeline, OCR disabled, table structure disabled) + Markdown header splitting                                                      |
| Layer 1: Concept matching | Embeds query, searches `document_concepts` by cosine similarity. Top-K=3, threshold=0.3. Narrows scope to chunks belonging to matched concepts. |
| Layer 2: Chunk retrieval  | PGVector similarity search on chunks, filtered by `document_id` and scoped by matched concepts. Concept summaries augment the search query.     |
| Fallback                  | If no concepts score above 0.3 (or no concepts exist for the documents), falls back to plain similarity search filtered only by `document_id`.  |
| Max chunks returned       | Configurable via `MAX_RETRIEVED_CHUNKS` setting (default: 20)                                                                                   |
| Deduplication             | Results are deduplicated before return                                                                                                          |

#### What breaks retrieval

- `doc_ids` is empty: returns immediately with zero chunks and `retrieval_status.error = "No doc_ids provided"`.
- `user_id` is missing: returns immediately with zero chunks and `retrieval_status.error = "Missing user_id"`.
- Ollama is unreachable: the embedding call will timeout or raise a connection error. The retrieval node catches this and returns empty chunks (the graph continues to `chat_model` with a fallback message).
- No pgvector extension: all similarity queries will fail with a SQL error.

---

## What a First-Time Contributor Would Likely Misunderstand

1. **The Ollama base URL is hardcoded.** `src/agents/utils/llm_config.py` hardcodes `base_url="http://ollama:11434"` for the embedding model. This works inside Docker (where `ollama` resolves via Docker DNS) but fails in local dev. There is no env var override wired in -- you must either set `OLLAMA_BASE_URL` and modify the code, or always run via Docker. The `docker-compose.yml` worker service sets `OLLAMA_BASE_URL` as an env var, but `llm_config.py` does not read it.

2. **Two graphs are compiled at startup, but only one is actively used.** `src/api/v1/main.py` compiles both `graph_builder` (from `src/agents/graph.py`) and `chat_builder` (from `src/agents/chat_agent.py`). The `chat_builder` is the active graph powering the chat endpoint. `graph_builder` is the older "generation SSE flow" graph, still compiled but likely vestigial. A contributor might edit the wrong graph.

3. **Migrations have no tracking.** There is no `schema_migrations` table or version file. If you run `docker compose down -v` and recreate the database, you must re-run all four migration files. There is no way to know which migrations have been applied other than inspecting the schema manually. The `add_dedup_lean.sql` file does not follow the numeric naming convention, which makes ordering ambiguous -- it should be run last.
