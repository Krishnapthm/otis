# Contributing

## Development Workflow

1. Create a feature branch from `main`:
   - `feature/<short-topic>` for new work
   - `fix/<short-topic>` for bug fixes
2. Keep PRs scoped to one concern (API contract, frontend UX, retrieval logic, etc.).
3. Update docs in the same PR when behavior or contracts change.

## Local Setup

- Backend deps: `uv sync`
- Frontend deps: `cd frontend/otis-ui && npm install`
- Run API: `uv run uvicorn src.api.v1.main:app --host 0.0.0.0 --port 8000 --reload`
- Run worker: `uv run -m src.worker`
- Run frontend: `cd frontend/otis-ui && npm run dev`

## Testing

### Backend

- Current focused test suite:
  - `uv run -m unittest tests/test_security_tokens.py`

### Frontend

- Unit tests (Vitest):
  - `cd frontend/otis-ui && npm run test`

## Linting and Build Checks

- Frontend lint:
  - `cd frontend/otis-ui && npm run lint`
- Frontend build:
  - `cd frontend/otis-ui && npm run build`

## Database Migrations

Migrations are raw SQL files in `migrations/` and must be applied in order.

Example (Docker db service):

- `docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/001_vectorstore_refactor.sql`
- `docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/002_document_concepts.sql`
- `docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/003_chat_message_events.sql`
- `docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /dev/stdin < migrations/add_dedup_lean.sql`

When adding schema changes:

1. Add a new SQL migration file in `migrations/`.
2. Update ORM/Pydantic definitions in `src/api/db/models/` and `src/api/db/schema.py`.
3. Update API/docs references in the same PR.

## PR Conventions

- Include a concise problem statement and solution summary.
- List behavior changes and any contract changes.
- Include test commands run and outcomes.
- If frontend/backend contract changed, note both sides explicitly.
