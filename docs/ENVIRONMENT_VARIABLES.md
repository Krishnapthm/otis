# Environment Variable Matrix

This is the canonical environment-variable reference for Otis.

## `.env` (infrastructure + shared)

| Variable                   | Required              | Used by                           | Purpose                                  |
| -------------------------- | --------------------- | --------------------------------- | ---------------------------------------- |
| `OPENAI_API_KEY`           | Yes                   | API, worker                       | OpenAI API key used by LangChain clients |
| `LANGSMITH_TRACING`        | No                    | API, worker                       | Enables LangSmith tracing                |
| `LANGSMITH_ENDPOINT`       | No                    | API, worker                       | LangSmith endpoint                       |
| `LANGSMITH_API_KEY`        | No                    | API, worker                       | LangSmith API key                        |
| `LANGSMITH_PROJECT`        | No                    | API, worker                       | LangSmith project name                   |
| `POSTGRES_USER`            | Yes                   | db, API/worker connection strings | Postgres user                            |
| `POSTGRES_PASSWORD`        | Yes                   | db, API/worker connection strings | Postgres password                        |
| `POSTGRES_DB`              | Yes                   | db, API/worker connection strings | Postgres database name                   |
| `PGADMIN_DEFAULT_EMAIL`    | No                    | pgadmin                           | pgAdmin login email                      |
| `PGADMIN_DEFAULT_PASSWORD` | No                    | pgadmin                           | pgAdmin login password                   |
| `VITE_API_BASE_URL`        | Yes (frontend builds) | frontend                          | Compile-time API base URL                |

## `.env.fastapi` (application settings)

| Variable                         | Required             | Used by                       | Purpose                                           |
| -------------------------------- | -------------------- | ----------------------------- | ------------------------------------------------- |
| `DB_URL`                         | Yes                  | API (`src/core/config.py`)    | Async SQLAlchemy connection URL                   |
| `JWT_SECRET_KEY`                 | Yes                  | API (`src/core/config.py`)    | JWT signing key                                   |
| `JWT_ALGORITHM`                  | No                   | API (`src/core/config.py`)    | JWT algorithm (default `HS256`)                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES`    | No                   | API (`src/core/config.py`)    | Access token TTL                                  |
| `REFRESH_TOKEN_EXPIRE_DAYS`      | No                   | API (`src/core/config.py`)    | Refresh token TTL                                 |
| `REDIS_URL`                      | No                   | API + worker                  | Redis URL for RQ and refresh-token JTI store      |
| `CORS_ORIGINS`                   | No                   | API (`src/core/config.py`)    | Allowed frontend origins                          |
| `NUM_SEARCH_QUERIES`             | No                   | API (`src/core/config.py`)    | Planner retrieval-query count                     |
| `MAX_RETRIEVED_CHUNKS`           | No                   | API (`src/core/config.py`)    | Retrieval chunk cap (default 20)                  |
| `USE_NAIVE_MCQ_GENERATOR`        | No                   | API (`src/core/config.py`)    | Toggle naive MCQ generator path                   |
| `CHAT_GRAPH_RETRIEVAL_ENABLED`   | No                   | API (`src/core/config.py`)    | Toggle retrieval inside graph path                |
| `CHAT_ROUTER_RETRIEVAL_FALLBACK` | No                   | API (`src/core/config.py`)    | Toggle router pre-retrieval fallback              |
| `TOKEN_CHUNK_SIZE`               | No                   | API (`src/core/config.py`)    | Event persistence token buffer size               |
| `TOKEN_CHUNK_FLUSH_MS`           | No                   | API (`src/core/config.py`)    | Event persistence token buffer flush interval     |
| `UPLOAD_DIR`                     | No                   | API/services                  | Upload storage directory                          |
| `THUMBNAIL_DIR`                  | No                   | API/services                  | Thumbnail storage directory                       |
| `OLLAMA_BASE_URL`                | No                   | API/worker                    | Ollama base URL for embeddings                    |
| `CONCEPT_LLM_DEPLOYMENT`         | No                   | worker (`concept_service.py`) | Azure deployment for concept extraction           |
| `CONCEPT_LLM_API_VERSION`        | No                   | worker (`concept_service.py`) | Azure API version for concept extraction          |
| `RETRIEVAL_DATABASE_URL`         | No                   | retrieval service             | Preferred sync PGVector retrieval URL             |
| `REDIS_DATABASE_URL`             | No (legacy fallback) | retrieval service             | Legacy fallback var name used as retrieval DB URL |

## Notes

- `.env` and `.env.fastapi` are both loaded by Docker Compose for API/worker containers; `Settings` itself reads `.env.fastapi`.
- `VITE_API_BASE_URL` is compile-time for frontend bundles; changing it requires rebuilding/restarting Vite.
- `agentApi.ts` currently hardcodes `http://localhost:8000`, so it does not fully honor `VITE_API_BASE_URL` until that frontend bug is fixed.
