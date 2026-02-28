# BACKEND_REFERENCE.md

**TL;DR:** This document is an encyclopedic reference for every Python module in the Otis backend. It covers function signatures, parameter types, return values, failure modes, and side effects for everything under `src/`. When the code and this document disagree, the code is correct.

---

## Assumptions

1. The canonical ORM models live in `src/api/db/models/__init__.py` (532 lines). The root-level `models.py` (361 lines) is a dead/legacy file containing LangGraph checkpoint tables and duplicate model definitions -- it is not imported anywhere in the active codebase.
2. All routers are mounted under the `/v1` prefix via `src/api/v1/main.py`. The older `src/api/routers/` directory contains leftover stubs (`docs.py`, `mcqs.py`) that are not wired into the FastAPI app.
3. The embedding pipeline uses `nomic-embed-text` (768-dimension vectors) via Ollama. The concept-extraction LLM defaults to `gpt-4.1-nano` via Azure OpenAI.
4. The RQ worker (`src/worker.py`) runs synchronously -- it cannot use asyncpg. All worker-side DB access uses a sync SQLAlchemy `Session`.
5. The deprecated `src/agents/graph.py` is compiled at startup and stored in `app.state.compiled_graph` but is only reachable via the `/v1/graph/start` endpoint. The active chat agent is `src/agents/chat_agent.py`, compiled into `app.state.compiled_chat_graph`.
6. Redis is optional for refresh-token storage in `src/core/security.py`. If unavailable, an in-memory dict is used as fallback.
7. All timestamps stored in chat-related tables use timezone-aware `DateTime(timezone=True)`. Project and MCQ timestamps are naive UTC, converted to IST at the CRUD layer.

---

## 4.1 Module Map

```text
src/
|-- __init__.py
|-- file_handling.py                 # DEAD CODE (superseded by src/services/file_handling.py)
|-- graph.py                         # DEAD CODE (superseded by src/agents/graph.py)
|-- mcq.py                           # DEAD CODE (superseded by src/agents/mcq.py)
|-- worker.py                        # RQ worker entry point
|
|-- core/                            # [CORE] Configuration, hashing, security
|   |-- __init__.py
|   |-- config.py
|   |-- hashing.py
|   |-- security.py
|
|-- api/                             # [API] FastAPI application layer
|   |-- __init__.py                  # Empty
|   |-- constants.py                 # Event type string constants
|   |-- db/
|   |   |-- __init__.py              # Empty
|   |   |-- schema.py                # Pydantic request/response schemas
|   |   |-- models/
|   |       |-- __init__.py          # Canonical ORM models (532 lines)
|   |       |-- session.py           # Async engine + session factory
|   |-- crud/
|   |   |-- __init__.py              # Re-exports all CRUD functions
|   |   |-- chat.py                  # Chat + message + event CRUD (699 lines)
|   |   |-- docs.py                  # Document CRUD with dedup logic (570 lines)
|   |   |-- embeddings.py            # Vectorstore lifecycle + RQ job dispatch
|   |   |-- mcq.py                   # MCQ CRUD (hardcoded IST timezone)
|   |   |-- projects.py              # Project CRUD with admin bypass
|   |   |-- users.py                 # Registration, login, token refresh
|   |-- utils/
|   |   |-- __init__.py              # TokenChunkBuffer, EventSequencer
|   |   |-- streaming.py             # Unused (5 lines, empty)
|   |-- routers/                     # DEAD — not mounted in app
|   |   |-- docs.py
|   |   |-- mcqs.py
|   |-- v1/
|       |-- main.py                  # FastAPI app, lifespan, router mounting
|       |-- routers/
|           |-- auth.py              # 7 endpoints
|           |-- chat.py              # 12 endpoints + SSE streaming
|           |-- docs.py              # 10 endpoints (project-scoped + user-scoped)
|           |-- projects.py          # 4 endpoints
|           |-- embeddings.py        # 3 endpoints
|           |-- mcqs.py              # 4 primary + legacy alias endpoints
|           |-- agent.py             # 2 endpoints (graph start/resume)
|
|-- services/                        # [SERVICES] Business logic
|   |-- __init__.py                  # Empty
|   |-- embedding_service.py         # DEPRECATED — superseded by embedding_tasks.py
|   |-- concept_service.py           # Concept extraction + chunk classification + storage
|   |-- retrieval_service.py         # Two-layer RAG retrieval
|   |-- file_handling.py             # File I/O, hashing, zip, thumbnails
|   |-- utils/
|       |-- export_utils.py          # MCQ export mode shaper + md/json/pdf/docx formatters
|
|-- tasks/                           # [TASKS] Background jobs (RQ)
|   |-- embedding_tasks.py           # Full embedding pipeline
|
|-- agents/                          # [AGENTS] LangGraph agent graphs and nodes
    |-- __init__.py                  # Empty
    |-- chat_agent.py                # Active chat/MCQ graph builder
    |-- graph.py                     # DEPRECATED — legacy RAG graph
    |-- mcq.py                       # Legacy MCQ generation (not used by chat_agent)
    |-- mcq_subgraph.py              # Per-question subgraph (stem -> options -> validator)
    |-- main.py                      # Minimal entry (6 lines, unused)
    |-- nodes/
    |   |-- __init__.py              # Re-exports all node functions
    |   |-- schemas.py               # Pydantic schemas for structured LLM output
    |   |-- scope.py                 # Scope classifier node (ALLOW/BLOCK)
    |   |-- intent.py                # Intent classifier node (4 classes)
    |   |-- planner.py               # MCQ plan generation node
    |   |-- retrieval.py             # Document retrieval node
    |   |-- chat.py                  # Chat response nodes (no-tools + with-tools stub)
    |   |-- output.py                # MCQ assembly + metadata finalization
    |   |-- validator.py             # MCQ draft validation node
    |   |-- generation/
    |       |-- __init__.py          # Re-exports stem + options generators
    |       |-- stem.py              # Question stem generator
    |       |-- options.py           # Options + correct answer generator
    |       |-- finalize.py          # DEAD CODE (duplicated in mcq_subgraph.py)
    |-- prompts/
    |   |-- __init__.py              # PROMPT_REGISTRY dict
    |   |-- chat.py                  # chat_no_tools_prompt
    |   |-- classification.py        # scope_classifier_prompt, intent_classifier_prompt
    |   |-- generation.py            # stem_generation_prompt, options_generation_prompt
    |   |-- planner.py               # planner_prompt
    |   |-- validator.py             # validator_prompt
    |-- utils/
        |-- __init__.py              # Empty
        |-- state.py                 # All TypedDicts and Pydantic models for graph state
        |-- llm_config.py            # Centralized LLM/embedding model instances
        |-- helpers.py               # Pure utility functions for nodes
        |-- nodes.py                 # Legacy AgentNodes class (used by deprecated graph.py)
        |-- prompts.py               # Legacy PROMPTS dict (used by nodes.py)
        |-- services/
            |-- __init__.py          # Empty
            |-- retrieval.py         # PGVector retrieval for agent nodes
            |-- concept_service.py   # Fetch concept map from DB
            |-- document_service.py  # Fetch document content from DB
```

---

## 4.2 Core (`src/core/`)

### 4.2.1 `config.py`

Defines the `Settings` class using `pydantic-settings`.

```python
class Settings(BaseSettings):
    db_url: str                          # env: DB_URL — async PostgreSQL URL (asyncpg)
    jwt_secret_key: str                  # env: JWT_SECRET_KEY
    jwt_algorithm: str = "HS256"         # env: JWT_ALGORITHM
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    num_search_queries: int = 5
    max_retrieved_chunks: int = 20
    use_naive_mcq_generator: bool = False
    chat_graph_retrieval_enabled: bool = True
    chat_router_retrieval_fallback: bool = False
    token_chunk_size: int = 50           # Flush buffer after this many chars
    token_chunk_flush_ms: int = 200      # Flush buffer after this many ms

    @property
    def checkpoint_db_url(self) -> str   # Strips "+asyncpg" for sync checkpoint driver
```

**Singleton:** `settings = Settings()` is instantiated at module level. There is no `get_settings()` function -- `settings` is imported directly.

**Env file:** Loaded from `.env.fastapi` via `SettingsConfigDict(env_file=".env.fastapi", extra="ignore")`.

**Related retrieval env vars (outside `Settings`):**

- `RETRIEVAL_DATABASE_URL` — preferred PGVector sync connection URL for retrieval service.
- `REDIS_DATABASE_URL` — legacy fallback name used by retrieval service when `RETRIEVAL_DATABASE_URL` is unset.

### 4.2.2 `hashing.py`

| Function                        | Signature                      | Return              | Notes                                                                                                                                                           |
| ------------------------------- | ------------------------------ | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `compute_file_hash_streaming`   | `(file_path: str) -> str`      | 64-char hex SHA-256 | Reads in 8KB chunks. Raises `FileNotFoundError`/`PermissionError` on I/O failure (no fallback).                                                                 |
| `compute_file_hash_from_stream` | `(file_obj: IO[bytes]) -> str` | 64-char hex SHA-256 | Reads in 8KB chunks from an open file object. Does not seek back to start.                                                                                      |
| `normalize_text`                | `(text: str) -> str`           | Normalized string   | NFC unicode normalization, lowercase, whitespace collapse, zero-width char removal.                                                                             |
| `compute_content_hash`          | `(text: str) -> str`           | 64-char hex SHA-256 | Normalizes text first via `normalize_text()`, then hashes. Two documents with identical text produce the same hash regardless of whitespace/casing differences. |

**Buffer size:** `BUFFER_SIZE = 8192` (8KB).

**Failure behavior:** Unlike the spec suggestion, these functions do NOT return a hash of empty string on I/O error. They propagate the underlying exception. The embedding task catches these exceptions at a higher level.

### 4.2.3 `security.py`

**Dependencies:** `python-jose` (JWT), `passlib[bcrypt]` (password hashing), optional `redis`.

**Module-level state:**

- `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`
- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")`
- `_refresh_token_store: dict[str, tuple[str, int]]` -- in-memory fallback when Redis is unavailable.
- `_redis_client` -- initialized at import time; set to `None` if Redis connection fails.

| Function                | Signature                                             | Behavior                                                                    | Failure                                                                                                                    |
| ----------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `verify_password`       | `(plain_password: str, hashed_password: str) -> bool` | bcrypt verify                                                               | Returns `False` on mismatch                                                                                                |
| `get_password_hash`     | `(password: str) -> str`                              | bcrypt hash                                                                 | Raises on invalid input                                                                                                    |
| `_create_token`         | `(data, token_type, expires_delta, jti?) -> str`      | Internal; creates JWT with `exp`, `typ`, `jti` claims                       | --                                                                                                                         |
| `create_access_token`   | `(data: dict, expires_delta?) -> str`                 | Creates JWT with `typ="access"`                                             | Default: 30 min expiry                                                                                                     |
| `create_refresh_token`  | `(data: dict, expires_delta?) -> str`                 | Creates JWT with `typ="refresh"`                                            | Default: 7 day expiry                                                                                                      |
| `decode_token`          | `(token: str, expected_type?) -> dict`                | Decodes + verifies JWT. Checks `typ` claim if `expected_type` given         | Raises `JWTError`                                                                                                          |
| `store_refresh_jti`     | `(subject: str, jti: str) -> None`                    | Stores JTI in Redis (with TTL) or in-memory dict                            | Silent fallback to memory                                                                                                  |
| `validate_refresh_jti`  | `(subject: str, jti: str) -> bool`                    | Checks stored JTI matches. Evicts expired entries from in-memory store      | Returns `False` on miss/expiry                                                                                             |
| `revoke_refresh_jti`    | `(subject: str) -> None`                              | Deletes stored JTI                                                          | No-op if missing                                                                                                           |
| `get_current_user`      | `(token, db) -> AuthResponse`                         | FastAPI dependency. Decodes access token, looks up user by email            | Raises `HTTPException(401)` on invalid/expired token or missing user                                                       |
| `verify_project_access` | `(project_id, current_user, db) -> Projects`          | FastAPI dependency. Checks project exists and user owns it (admin bypasses) | Raises `HTTPException(404)` on missing project or access denied (note: returns 404, not 403, to avoid information leakage) |

**Typo in source:** Parameter `plain_passowrd` (sic) in `verify_password`.

---

## 4.3 ORM Models (`src/api/db/models/__init__.py`)

**Canonical location:** `src/api/db/models/__init__.py` (532 lines).

**Dead code:** `models.py` (root) contains a duplicate set of model definitions including LangGraph checkpoint tables (`CheckpointBlobs`, `CheckpointMigrations`, `CheckpointWrites`, `Checkpoints`). These are managed by LangGraph's `AsyncPostgresSaver.setup()` at startup and are NOT defined in the canonical models file. The root `models.py` file is not imported by any active module.

### Model Reference Table

| Table Name                | Class                       | Primary Key            | Foreign Keys                                                                                 | Notable Indexes                                                                              |
| ------------------------- | --------------------------- | ---------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `users`                   | `Users`                     | `user_id` (UUID)       | --                                                                                           | `UNIQUE(email)`                                                                              |
| `documents`               | `Documents`                 | `doc_id` (UUID)        | `user_id -> users.user_id (CASCADE)`, `canonical_document_id -> documents.doc_id (SET NULL)` | --                                                                                           |
| `projects`                | `Projects`                  | `project_id` (UUID)    | --                                                                                           | --                                                                                           |
| `project_docs`            | `t_project_docs` (junction) | `(project_id, doc_id)` | `project_id -> projects`, `doc_id -> documents` (both CASCADE)                               | --                                                                                           |
| `project_mcqs`            | `t_project_mcqs` (junction) | `(project_id, mcq_id)` | `project_id -> projects`, `mcq_id -> mcqs` (both CASCADE)                                    | --                                                                                           |
| `mcqs`                    | `Mcqs`                      | `mcq_id` (UUID)        | --                                                                                           | --                                                                                           |
| `chats`                   | `Chats`                     | `chat_id` (UUID)       | `user_id -> users.user_id (CASCADE)`                                                         | `idx_chats_user_id`, `idx_chats_status`, `idx_chats_last_message_at`                         |
| `chat_messages`           | `ChatMessages`              | `message_id` (UUID)    | `chat_id -> chats.chat_id (CASCADE)`                                                         | `idx_messages_chat_id`, `idx_messages_chat_sequence`                                         |
| `chat_message_events`     | `ChatMessageEvents`         | `event_id` (UUID)      | `message_id -> chat_messages.message_id (CASCADE)`                                           | `idx_message_events_message_id`, `idx_message_events_message_seq`, `UNIQUE(message_id, seq)` |
| `chat_message_documents`  | `ChatMessageDocuments`      | `cmd_id` (UUID)        | `message_id -> chat_messages`, `doc_id -> documents` (both CASCADE)                          | --                                                                                           |
| `langchain_pg_collection` | `LangchainPgCollection`     | `uuid` (UUID)          | --                                                                                           | `UNIQUE(name)`                                                                               |
| `langchain_pg_embedding`  | `LangchainPgEmbedding`      | `id` (String)          | `collection_id -> langchain_pg_collection.uuid (CASCADE)`                                    | `ix_cmetadata_gin` (JSONB GIN)                                                               |
| `user_vectorstores`       | `UserVectorstore`           | `user_id` (UUID)       | `user_id -> users (CASCADE)`, `collection_id -> langchain_pg_collection.uuid (SET NULL)`     | --                                                                                           |
| `concept_cache`           | `ConceptCache`              | `cache_id` (UUID)      | --                                                                                           | `UNIQUE(content_hash, extractor_version)`                                                    |
| `mcq_cache`               | `MCQCache`                  | `cache_id` (UUID)      | --                                                                                           | `UNIQUE(concept_set_id, generator_version, params_hash)`                                     |
| `document_concepts`       | `DocumentConcept`           | `concept_id` (UUID)    | `document_id -> documents.doc_id (CASCADE)`                                                  | `idx_document_concepts_doc_id`, `UNIQUE(document_id, concept_name)`                          |

### Key Column Details

**Documents:**

- `status`: `pending | processing | ready | failed` (default: `pending`)
- `file_hash`: SHA-256 of raw file bytes (for file-level dedup)
- `content_hash`: SHA-256 of normalized markdown text (for content-level dedup)
- `canonical_document_id`: Points to another document with the same `content_hash` when content-level dedup triggers. The duplicate inherits the canonical doc's embeddings without re-embedding.
- `is_embedded` / `embedded_at`: Track embedding pipeline completion.
- `content_md`: Full markdown extracted by Docling/pymupdf4llm. Populated during embedding, not at upload.

**Chats:**

- `status`: CHECK constraint: `active | archived | deleted`
- Soft-delete pattern: `status = 'deleted'` + `deleted_at` timestamp. Row is never physically removed.

**ChatMessages:**

- `role`: CHECK constraint: `user | assistant | tool`
- `status`: CHECK constraint: `pending | streaming | completed | failed`
- `sequence`: Monotonically increasing per chat. Computed as `MAX(sequence) + 1` at insert time.
- `structured_data`: JSONB column for MCQ artifacts, tool results, etc.

**ChatMessageEvents:**

- `seq`: Per-message monotonic counter. `UNIQUE(message_id, seq)` constraint.
- `event_type`: Unconstrained TEXT column. Convention-only types defined in `src/api/constants.py`.
- `metadata_`: Mapped from column name `metadata` (trailing underscore avoids Python keyword conflict).

**UserVectorstore:**

- One-to-one with `Users` (PK = `user_id`).
- `status`: `pending | processing | ready | failed`
- `job_id`: RQ job identifier for the in-progress embedding task.

**DocumentConcept:**

- `concept_embedding`: `VECTOR(768)` -- matches `nomic-embed-text` output dimension.
- Used for Layer 1 concept matching in the two-layer retrieval algorithm.

---

## 4.4 Pydantic Schemas (`src/api/db/schema.py`)

### Auth Schemas

| Schema                | Purpose                | Notable Fields                                                                              |
| --------------------- | ---------------------- | ------------------------------------------------------------------------------------------- |
| `CreateUser`          | Registration request   | `email`, `uname`, `password` (validated: min 8 chars, 1 upper, 1 lower, 1 digit, 1 special) |
| `LoginUser`           | Login request          | `email`, `password`                                                                         |
| `AuthResponse`        | Current user identity  | `user_id: UUID4`, `uname`, `email`, `role: Literal["admin", "user"]`                        |
| `Token`               | JWT response           | `access_token`, `token_type`, `refresh_token?`                                              |
| `TokenData`           | Internal token payload | `email?`                                                                                    |
| `RefreshTokenRequest` | Refresh request        | `refresh_token: str`                                                                        |
| `UserUpdateRequest`   | Edit user              | `uname?`, `email?`, `password?` (all optional)                                              |
| `UserResponse`        | User detail response   | `id: UUID4`, `uname`, `email`, `created_at`                                                 |

### Document Schemas

| Schema           | Purpose                  | Notable Fields                                                                                                          |
| ---------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `DocBase`        | Internal upload metadata | `filename`, `file_type`, `file_size`, `file_path`, `file_hash?`                                                         |
| `DocResponse`    | Document response        | Extends `DocBase` + `doc_id`, `user_id`, `project_id?`, `created_at`, `is_embedded`, `status`, `canonical_document_id?` |
| `DocDelete`      | Delete request           | `doc_id: List[uuid.UUID]`                                                                                               |
| `DocLinkRequest` | Link docs to project     | `doc_ids: List[uuid.UUID]`                                                                                              |

### Vectorstore/Embedding Schemas

| Schema                    | Purpose         | Notable Fields                                                                                      |
| ------------------------- | --------------- | --------------------------------------------------------------------------------------------------- |
| `VectorstoreStatus`       | Status response | `user_id`, `status`, `total_documents`, `embedded_documents`, `pending_documents`, `error_message?` |
| `VectorstoreSyncRequest`  | Sync request    | `doc_ids?: List[uuid.UUID]` (if empty, sync all pending)                                            |
| `VectorstoreSyncResponse` | Sync response   | `status`, `message`, `documents_queued`, `job_id?`                                                  |

### Project Schemas

| Schema            | Purpose       | Notable Fields                           |
| ----------------- | ------------- | ---------------------------------------- |
| `ProjectBase`     | Create/update | `project_name`, `project_desc?`          |
| `ProjectResponse` | Response      | `project_id`, `created_at`, `created_by` |

### MCQ Schemas

| Schema      | Purpose             | Notable Fields                                                                                          |
| ----------- | ------------------- | ------------------------------------------------------------------------------------------------------- |
| `Options`   | Single MCQ option   | `key: Literal["A","B","C","D"]`, `text`                                                            |
| `Questions` | Single MCQ question | `question_index: int`, `question`, `options: List[Options]`, `right_answer`, `explanation`             |
| `MCQ`       | MCQ collection      | `test_id`, `doc_ids`, `plan`, `questions`, `test_name`, `created_at`                                   |
| `CreateMCQ` | Create request      | `mcq: MCQ`                                                                                              |
| `ReadMCQ`   | Read response       | Extends `CreateMCQ` + `mcq_id`                                                                          |

### Agent/Graph Schemas

| Schema                    | Purpose              | Notable Fields                                                                      |
| ------------------------- | -------------------- | ----------------------------------------------------------------------------------- |
| `StartGraphRequest`       | Start MCQ graph      | `doc_ids: List[uuid.UUID]`, `user_prompt?`                                          |
| `Concept`                 | A concept            | `name`, `summary`                                                                   |
| `DocumentConceptResponse` | Concept API response | `concept_id`, `document_id`, `concept_name`, `concept_summary`, `extractor_version` |
| `ConceptMatchResult`      | Layer-1 match result | `concept_name`, `concept_summary`, `score: float`                                   |
| `ResumeRequest`           | Resume graph         | `selected_concepts: List[Concept]`                                                  |

### Chat Schemas

| Schema                           | Purpose          | Notable Fields                                                                                        |
| -------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------- |
| `ChatCreate`                     | Create chat      | `title?`                                                                                              |
| `ChatUpdate`                     | Update chat      | `title?`, `status?: active/archived/deleted`                                                          |
| `ChatResponse`                   | Chat response    | `chat_id`, `user_id`, `status`, `total_input_tokens`, `total_output_tokens`, `title?`                 |
| `ChatMessageCreate`              | Create message   | `role`, `content?`, `structured_data?`, `doc_ids?`, `status`                                          |
| `ChatMessageUpdate`              | Update message   | All fields optional                                                                                   |
| `ChatMessageResponse`            | Message response | `message_id`, `chat_id`, `role`, `sequence`, `status`, `content?`, `doc_ids: List[UUID4]`             |
| `ChatMessageEventResponse`       | Single event     | `event_id`, `message_id`, `seq`, `event_type`, `content?`, `metadata?`                                |
| `ChatMessageEventReplayResponse` | Event batch      | `events: List`, `is_complete: bool`, `last_seq: int`                                                  |
| `ChatInvokeRequest`              | Invoke chat      | `message`, `doc_ids?`, `mentions?`, `edit_mode: bool`, `edit_target`, `edit_indices`, `edit_strategy` |

---

## 4.5 Routers (`src/api/v1/routers/`)

### 4.5.1 `auth.py` -- 7 Endpoints

| Method | Path                | Auth   | Request                     | Response       | Status | Notes                                                          |
| ------ | ------------------- | ------ | --------------------------- | -------------- | ------ | -------------------------------------------------------------- |
| POST   | `/v1/auth/register` | None   | `CreateUser`                | `UserResponse` | 201    | Raises 400 if email exists                                     |
| POST   | `/v1/auth/login`    | None   | `OAuth2PasswordRequestForm` | `Token`        | 200    | Returns access + refresh tokens                                |
| GET    | `/v1/auth/me`       | Bearer | --                          | `AuthResponse` | 200    | Returns current user info                                      |
| POST   | `/v1/auth/logout`   | Bearer | --                          | `dict`         | 200    | Revokes refresh token JTI                                      |
| POST   | `/v1/auth/refresh`  | None   | `RefreshTokenRequest`       | `Token`        | 200    | Rotates refresh token, issues new access token                 |
| DELETE | `/v1/auth/delete`   | Bearer | --                          | `dict`         | 200    | Deletes user row, revokes refresh JTI                          |
| PUT    | `/v1/auth/edit`     | Bearer | `UserUpdateRequest`         | `UserResponse` | 200    | Updates user fields; checks email uniqueness (409 on conflict) |

All 7 endpoints are fully implemented. The spec mentioned stubs -- this is no longer the case; `logout`, `refresh`, `delete`, and `edit` are all functional.

### 4.5.2 `chat.py` -- 12 Endpoints

| Method | Path                                               | Auth   | Request                               | Response                                | Status | Notes                                                                |
| ------ | -------------------------------------------------- | ------ | ------------------------------------- | --------------------------------------- | ------ | -------------------------------------------------------------------- |
| POST   | `/v1/chats/`                                       | Bearer | `ChatCreate`                          | `ChatResponse`                          | 201    |                                                                      |
| GET    | `/v1/chats/`                                       | Bearer | query: `limit`, `skip`, `chat_status` | `List[ChatResponse]`                    | 200    | Excludes deleted by default                                          |
| GET    | `/v1/chats/{chat_id}`                              | Bearer | --                                    | `ChatResponse`                          | 200    | 404 if not owned                                                     |
| PATCH  | `/v1/chats/{chat_id}`                              | Bearer | `ChatUpdate`                          | `ChatResponse`                          | 200    | Supports soft-delete via `status="deleted"`                          |
| DELETE | `/v1/chats/{chat_id}`                              | Bearer | --                                    | `dict`                                  | 200    | Soft-delete (sets `status="deleted"`)                                |
| POST   | `/v1/chats/{chat_id}/messages`                     | Bearer | `ChatMessageCreate`                   | `ChatMessageResponse`                   | 201    | Increments sequence. Validates doc_ids ownership                     |
| GET    | `/v1/chats/{chat_id}/messages`                     | Bearer | query: `limit`, `skip`                | `List[ChatMessageResponse]`             | 200    | Ordered by sequence ASC                                              |
| GET    | `/v1/chats/{chat_id}/messages/{message_id}`        | Bearer | --                                    | `ChatMessageResponse`                   | 200    |                                                                      |
| PATCH  | `/v1/chats/{chat_id}/messages/{message_id}`        | Bearer | `ChatMessageUpdate`                   | `ChatMessageResponse`                   | 200    |                                                                      |
| DELETE | `/v1/chats/{chat_id}/messages/{message_id}`        | Bearer | --                                    | `dict`                                  | 200    | Hard-delete. Re-syncs chat aggregates                                |
| POST   | `/v1/chats/{chat_id}/invoke`                       | Bearer | `ChatInvokeRequest`                   | `StreamingResponse` (SSE)               | 200    | See SSE streaming section below                                      |
| GET    | `/v1/chats/{chat_id}/messages/{message_id}/events` | Bearer | query: `after_seq`                    | `ChatMessageEventReplayResponse` or SSE | 200    | Returns JSON if message is complete; SSE stream if still in-progress |

**SSE Streaming (`/invoke`):**

The invoke endpoint creates user + assistant messages, then returns an SSE `StreamingResponse`. The stream:

1. Transitions assistant message to `status="streaming"`.
2. Emits `started` event with `assistant_message_id`.
3. If `chat_router_retrieval_fallback` is enabled and `doc_ids` are present, runs two-layer retrieval before graph invocation, injecting context as a system message. Emits synthetic `thinking` events for the retrieval phase.
4. Streams graph output via `graph.astream()` with `stream_mode=["custom", "messages"]`.
5. `custom` events become `thinking` SSE events (node lifecycle updates).
6. `messages` events from terminal generation nodes (`chat_model`, `naive_mcq_generator_node`) become `token` SSE events. Tokens are accumulated in a `TokenChunkBuffer` for batched persistence.
7. Reasoning tokens (OpenAI o-series `reasoning_content`, Anthropic `thinking` blocks) are emitted as `reasoning_token` events.
8. On completion: flushes remaining tokens, emits `done` event, updates message to `status="completed"`.
9. On error: flushes partial tokens, emits `error` event, updates message to `status="failed"`.

All events are persisted to `chat_message_events` via `create_message_event()` for later replay.

**Event Replay (`/events`):**

For completed/failed messages, returns a JSON `ChatMessageEventReplayResponse` directly. For in-progress messages, returns an SSE stream that emits stored events, then polls every 500ms for new events until the message reaches a terminal state.

**Replay translation helper:** `_event_to_sse_line(event)` in `src/api/v1/routers/chat.py` maps persisted `chat_message_events.event_type` values (`started`, `thinking`, `token_chunk`, `reasoning_token`, `done`, `error`) back to frontend SSE payload shapes (`started`, `thinking`, `token`, `reasoning_token`, `done`, `error`).

### 4.5.3 `docs.py` -- 10 Endpoints (Two Routers)

**Project-Scoped Router** (prefix: `/v1/project/{project_id}/documents`):

| Method | Path        | Auth   | Request            | Response                                  | Status | Notes                                                        |
| ------ | ----------- | ------ | ------------------ | ----------------------------------------- | ------ | ------------------------------------------------------------ |
| POST   | `/`         | Bearer | `List[UploadFile]` | `List[DocResponse]`                       | 201    | Stores files via staging pattern. File-hash + filename dedup |
| POST   | `/link`     | Bearer | `DocLinkRequest`   | `dict`                                    | 200    | Idempotent link of existing docs to project                  |
| GET    | `/`         | Bearer | --                 | `List[DocResponse]`                       | 200    | All docs in project                                          |
| GET    | `/download` | Bearer | --                 | `FileResponse` or zip `StreamingResponse` | 200    | Single file or zip for multiple                              |
| GET    | `/{doc_id}` | Bearer | --                 | `DocResponse`                             | 200    | Single doc from project                                      |
| DELETE | `/`         | Bearer | `DocDelete`        | `dict`                                    | 200    | Deletes docs entirely (all projects). Cleans up embeddings   |

**User-Scoped Router** (prefix: `/v1/documents`):

| Method | Path                  | Auth   | Request                | Response             | Status | Notes                  |
| ------ | --------------------- | ------ | ---------------------- | -------------------- | ------ | ---------------------- |
| GET    | `/`                   | Bearer | query: `limit`, `skip` | `List[DocResponse]`  | 200    | All user's docs        |
| POST   | `/`                   | Bearer | `List[UploadFile]`     | `List[DocResponse]`  | 201    | Upload without project |
| GET    | `/{doc_id}`           | Bearer | --                     | `DocResponse`        | 200    |                        |
| GET    | `/{doc_id}/download`  | Bearer | --                     | `FileResponse`       | 200    |                        |
| GET    | `/{doc_id}/thumbnail` | Bearer | --                     | `FileResponse` (PNG) | 200    |                        |
| DELETE | `/`                   | Bearer | `DocDelete`            | `dict`               | 200    |                        |

**Side effects of upload:** File is first written to a staging directory (`UPLOAD_DIR/.staging/`), then moved to `UPLOAD_DIR/` after dedup checks pass. On duplicate detection, the staging file is deleted and a 409 is returned.

**Side effects of delete:** Removes file from disk, deletes embedding rows from `langchain_pg_embedding` where `cmetadata->>'document_id'` matches. The `DocumentConcept` rows are cascade-deleted via FK. Orphaned embeddings from chunks that were embedded under a different collection are NOT cleaned up (tech debt).

### 4.5.4 `projects.py` -- 4 Endpoints

| Method | Path                        | Auth   | Request                | Response                | Status | Notes                             |
| ------ | --------------------------- | ------ | ---------------------- | ----------------------- | ------ | --------------------------------- |
| POST   | `/v1/projects/`             | Bearer | `ProjectBase`          | `ProjectResponse`       | 201    |                                   |
| GET    | `/v1/projects/`             | Bearer | query: `limit`, `skip` | `List[ProjectResponse]` | 200    | Admin sees all; user sees own     |
| GET    | `/v1/projects/{project_id}` | Bearer | --                     | `ProjectResponse`       | 200    | Admin bypass on ownership check   |
| DELETE | `/v1/projects/{project_id}` | Bearer | --                     | `dict`                  | 200    | Hard-delete. Admin can delete any |

### 4.5.5 `embeddings.py` -- 3 Endpoints

| Method | Path                    | Auth   | Request                   | Response                  | Status | Notes                                                         |
| ------ | ----------------------- | ------ | ------------------------- | ------------------------- | ------ | ------------------------------------------------------------- |
| POST   | `/v1/embeddings/sync`   | Bearer | `VectorstoreSyncRequest?` | `VectorstoreSyncResponse` | 200    | Idempotent. Enqueues RQ job. Returns early if all docs synced |
| GET    | `/v1/embeddings/status` | Bearer | --                        | `VectorstoreStatus`       | 200    | Doc counts + vectorstore status                               |
| DELETE | `/v1/embeddings/clear`  | Bearer | --                        | `dict`                    | 200    | Deletes collection + embeddings, resets docs. Idempotent      |

### 4.5.6 `mcqs.py` -- MCQ + Export Endpoints

| Method | Path                         | Auth   | Request                                 | Response                                          | Status | Notes                                                                                              |
| ------ | ---------------------------- | ------ | --------------------------------------- | ------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| POST   | `/v1/mcqs/`                  | Bearer | `CreateMCQ`                             | `ReadMCQ`                                         | 201    | Auth required                                                                                      |
| GET    | `/v1/mcqs/`                  | Bearer | --                                      | `List[ReadMCQ]`                                   | 200    | Returns persisted MCQ tests                                                                        |
| GET    | `/v1/mcqs/download/{id}`     | Bearer | --                                      | `Response` (JSON file download)                   | 200    | Legacy JSON download endpoint; 404 returns plain text                                              |
| GET    | `/v1/mcqs/{mcq_id}/export`   | Bearer | query: `format` + `mode`                | `Response` (md/json/pdf/docx attachment)          | 200    | Multi-format export; `mode=test` strips `right_answer` and `explanation`                          |

Legacy aliases are mounted under `/v1/mcq/*` for create/list/download/export compatibility.

### 4.5.7 `agent.py` -- 2 Endpoints

| Method | Path                           | Auth   | Request             | Response                  | Status | Notes                                                                               |
| ------ | ------------------------------ | ------ | ------------------- | ------------------------- | ------ | ----------------------------------------------------------------------------------- |
| POST   | `/v1/graph/start`              | Bearer | `StartGraphRequest` | `StreamingResponse` (SSE) | 200    | Uses deprecated `graph.py` graph. Requires vectorstore `status="ready"`             |
| POST   | `/v1/graph/resume/{thread_id}` | Bearer | `ResumeRequest`     | `StreamingResponse` (SSE) | 200    | Resumes graph with `Command(resume=selected_concepts)`. Human-in-the-loop interrupt |

The `start` endpoint derives `collection_name = f"user_{user_id}"` from the authenticated user. It raises `HTTPException(400)` if the vectorstore is not ready.

The `resume` endpoint accepts a list of selected concepts and passes them as a LangGraph `Command(resume=...)` to the interrupted graph thread.

---

## 4.6 CRUD Layer (`src/api/crud/`)

### 4.6.1 `chat.py` (699 lines)

**Internal helpers:**

| Function                                                                   | Purpose                                                                                     |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `_is_admin(db, user_id) -> bool`                                           | Checks if user has `role="admin"`                                                           |
| `_get_chat_for_user(db, chat_id, current_user, include_deleted?) -> Chats` | Fetches chat with ownership check. Raises `HTTPException(404)`. Admin sees all chats        |
| `_sync_chat_aggregates(db, chat) -> None`                                  | Recomputes `total_input_tokens`, `total_output_tokens`, `last_message_at` from message rows |
| `_chat_to_response(chat) -> ChatResponse`                                  | ORM-to-Pydantic conversion                                                                  |
| `_message_to_response(message) -> ChatMessageResponse`                     | ORM-to-Pydantic conversion (always sets `doc_ids=[]`)                                       |
| `_dedupe_doc_ids(doc_ids) -> List[UUID]`                                   | Preserves insertion order, removes duplicates                                               |
| `_validate_doc_ids_for_user(db, current_user, doc_ids) -> List[UUID]`      | Verifies all doc_ids belong to user. Raises `HTTPException(404)` if any are missing         |
| `_replace_message_documents(db, message_id, doc_ids) -> None`              | Deletes existing `ChatMessageDocuments` rows and re-inserts                                 |
| `_get_message_doc_ids(db, message_ids) -> dict[UUID, List[UUID]]`          | Batch-fetches doc_ids for multiple messages                                                 |

**Public functions:**

| Function                     | Signature                                                                                       | DB Operations                                              | Side Effects                                                                   |
| ---------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `create_chat`                | `(db, payload: ChatCreate, current_user) -> ChatResponse`                                       | INSERT `chats`                                             | --                                                                             |
| `list_chats`                 | `(db, current_user, limit?, skip?, status?) -> List[ChatResponse]`                              | SELECT `chats` ordered by `updated_at DESC NULLS LAST`     | --                                                                             |
| `get_chat`                   | `(db, chat_id, current_user) -> ChatResponse`                                                   | SELECT with ownership check                                | --                                                                             |
| `update_chat`                | `(db, chat_id, payload: ChatUpdate, current_user) -> ChatResponse`                              | UPDATE `chats`. Sets `deleted_at` if status="deleted"      | Raises 400 if no fields to update                                              |
| `delete_chat`                | `(db, chat_id, current_user) -> dict`                                                           | UPDATE `chats` (soft-delete)                               | Idempotent: returns success if already deleted                                 |
| `create_chat_message`        | `(db, chat_id, payload, current_user) -> ChatMessageResponse`                                   | INSERT `chat_messages` + INSERT `chat_message_documents`   | Computes next `sequence`. Syncs chat aggregates. Raises 400 if chat is deleted |
| `list_chat_messages`         | `(db, chat_id, current_user, limit?, skip?, exclude_incomplete?) -> List[ChatMessageResponse]`  | SELECT ordered by `sequence ASC`                           | `exclude_incomplete=True` filters out pending/streaming/failed messages        |
| `get_chat_message`           | `(db, chat_id, message_id, current_user) -> ChatMessageResponse`                                | SELECT with chat+message join                              | --                                                                             |
| `update_chat_message`        | `(db, chat_id, message_id, payload, current_user) -> ChatMessageResponse`                       | UPDATE `chat_messages`. Replaces doc_ids if provided       | Syncs chat aggregates                                                          |
| `delete_chat_message`        | `(db, chat_id, message_id, current_user) -> dict`                                               | DELETE `chat_messages` (hard-delete)                       | Syncs chat aggregates. CASCADE deletes events + document links                 |
| `create_message_event`       | `(db, message_id, seq, event_type, content?, metadata?) -> ChatMessageEvents`                   | INSERT (does NOT flush)                                    | Caller must `db.flush()` / `db.commit()`                                       |
| `bulk_create_message_events` | `(db, events: List[dict]) -> None`                                                              | Batch INSERT + flush                                       | --                                                                             |
| `list_message_events`        | `(db, chat_id, message_id, current_user, after_seq?, limit?) -> ChatMessageEventReplayResponse` | SELECT events where `seq > after_seq` ordered by `seq ASC` | Returns `is_complete=True` if message status is `completed` or `failed`        |
| `get_latest_event_seq`       | `(db, message_id) -> int`                                                                       | SELECT MAX(seq)                                            | Returns 0 if no events                                                         |
| `mark_stale_messages_failed` | `(db) -> int`                                                                                   | UPDATE all `pending`/`streaming` messages to `failed`      | Called at startup for crash recovery. Commits immediately                      |

### 4.6.2 `docs.py` (570 lines)

| Function                | Signature                                                                   | Notes                                                                                                                                                                                                  |
| ----------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `upload_new_doc`        | `(project_id?, db, docs: List[DocBase], current_user) -> List[DocResponse]` | Two-level dedup: (1) `file_hash` match returns 409 with existing doc info, (2) `filename` match returns 409 with hint. Moves file from staging to `UPLOAD_DIR`. Links to project if `project_id` given |
| `link_docs_to_project`  | `(user_id, project_id, doc_ids, db) -> dict`                                | Idempotent. Returns `{linked, skipped}` counts. Verifies project ownership and doc ownership                                                                                                           |
| `get_user_docs`         | `(user_id, db, limit?, skip?) -> List[DocResponse]`                         | All docs owned by user, regardless of project                                                                                                                                                          |
| `get_user_doc_by_id`    | `(user_id, doc_id, db) -> DocResponse`                                      | Single doc with ownership check                                                                                                                                                                        |
| `get_doc`               | `(db, did, project_id, user_id) -> DocResponse`                             | Gets doc scoped to project (joins through `project_docs`)                                                                                                                                              |
| `get_all_docs`          | `(project_id, db, user_id, limit?, skip?) -> List[DocResponse]`             | All docs in a project (verifies project ownership)                                                                                                                                                     |
| `delete_doc`            | `(db, did: List[UUID], user_id) -> dict`                                    | Deletes file from disk, deletes embedding rows by `cmetadata->>'document_id'`, deletes ORM row. Raises 404 if no docs found                                                                            |
| `download_user_doc`     | `(db, doc_id, user_id) -> FileResponse`                                     | Single file download with ownership check                                                                                                                                                              |
| `download_project_docs` | `(db, project_id, user_id) -> FileResponse`                                 | Single file or zip; verifies project ownership                                                                                                                                                         |
| `download_doc`          | `(db, project_id, user_id) -> FileResponse`                                 | Alias for `download_project_docs` (backward compat)                                                                                                                                                    |
| `doc_thumbnail`         | `(doc_id, user_id, db) -> FileResponse`                                     | Calls `pdf_thumbnail()` from file_handling service. Ownership check                                                                                                                                    |

**Orphaned embedding tech debt:** When a document is deleted, only embeddings matching `cmetadata->>'document_id'` in the user's collection are deleted. If the document was ever embedded into a different collection (e.g., during a migration), those embeddings are orphaned.

### 4.6.3 `users.py` (175 lines)

| Function              | Signature                                             | Notes                                                                                                   |
| --------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `create_user`         | `(user_data: CreateUser, db) -> UserResponse`         | Hashes password via `get_password_hash()`. Raises 400 if email exists                                   |
| `login_user`          | `(form_data: OAuth2PasswordRequestForm, db) -> Token` | Verifies password. Creates access + refresh tokens. Stores refresh JTI. Raises 401 on bad credentials   |
| `refresh_user_token`  | `(refresh_token: str, db) -> Token`                   | Decodes refresh token, validates JTI, rotates to new refresh token. Raises 401 on invalid/expired token |
| `logout_user`         | `(current_user: AuthResponse) -> dict`                | Revokes refresh JTI. Returns `{"message": "Logged out successfully"}`                                   |
| `delete_current_user` | `(current_user, db) -> dict`                          | Hard-deletes user row. Revokes refresh JTI. CASCADE deletes documents, vectorstore, etc.                |
| `edit_current_user`   | `(payload, current_user, db) -> UserResponse`         | Updates email (checks uniqueness, 409 on conflict), uname, password.                                    |

### 4.6.4 `projects.py` (163 lines)

| Function                 | Signature                                                    | Notes                                                                               |
| ------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| `create_new_project`     | `(db, project, current_user) -> ProjectResponse`             | Converts `created_at` to IST for response                                           |
| `get_all_projects`       | `(db, current_user, limit?, skip?) -> List[ProjectResponse]` | Admin sees all projects                                                             |
| `get_project`            | `(db, pid, current_user?) -> ProjectResponse`                | Admin bypass. If `current_user` is None, no ownership check (legacy)                |
| `delete_project_with_id` | `(db, pid, current_user) -> dict`                            | Hard-delete. Admin can delete any project. Raises 404 if not found or no permission |

**Hardcoded IST timezone:** `IST = timezone(timedelta(hours=5, minutes=30))` is used to convert UTC timestamps in responses. This affects `created_at` display only -- the database stores UTC.

### 4.6.5 `embeddings.py` (262 lines)

| Function                    | Signature                                            | Notes                                                                                                                                                                     |
| --------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `get_or_create_vectorstore` | `(user_id, db) -> UserVectorstore`                   | Idempotent. Creates with `status="pending"` if missing                                                                                                                    |
| `sync_user_embeddings`      | `(user_id, db, doc_ids?) -> VectorstoreSyncResponse` | Filters docs with `is_embedded=False`. Returns early if nothing to embed. Short-circuits if already processing. Enqueues `process_user_embeddings` RQ job with 2h timeout |
| `get_vectorstore_status`    | `(user_id, db) -> VectorstoreStatus`                 | Counts total, embedded, pending documents                                                                                                                                 |
| `clear_user_vectorstore`    | `(user_id, db) -> dict`                              | Deletes LangChain collection (cascades to embeddings). Resets all user docs to `is_embedded=False`. Resets vectorstore status. Idempotent                                 |

**RQ job enqueueing:**

```python
queue.enqueue(
    process_user_embeddings,
    args=(str(user_id), collection_name, document_ids, file_paths),
    job_timeout="2h",
    failure_ttl=86400,    # Keep failed job info for 24h
    result_ttl=3600,      # Keep success result for 1h
)
```

This enqueue path intentionally uses positional `args=(...)` to match the worker function signature.

### 4.6.6 `mcq.py`

| Function       | Signature                                        | Notes                                                                                         |
| -------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `create_mcq`   | `(db, mcq: CreateMCQ) -> ReadMCQ`                | Persists normalized fields (`test_id`, `doc_ids`, `plan`, `questions`, `created_at`, `test_name`) |
| `get_mcq`      | `(db, mcq_id: UUID) -> Optional[list[ReadMCQ]]`  | Returns `None` if missing; otherwise list of normalized `ReadMCQ`                             |
| `get_all_mcqs` | `(db, limit?, skip?) -> list[ReadMCQ]`           | Ordered by `created_at DESC NULLS LAST`, then `generated_at DESC NULLS LAST`                 |

The CRUD layer now supports backward compatibility by coercing legacy MCQ payloads into the current schema (`question_index`, option `key`, `right_answer`).

**Design rationale note:** The unfiltered `get_all_mcqs` behavior currently acts as a shared MCQ pool for all authenticated users. Treat this as the current contract unless product requirements explicitly move MCQs to per-user ownership.

---

## 4.7 API Utilities (`src/api/utils/`)

### `TokenChunkBuffer`

Accumulates streaming tokens and yields persistence-ready chunks when either threshold is met:

- **Size threshold:** `token_chunk_size` (default: 50 chars from settings)
- **Time threshold:** `token_chunk_flush_ms` (default: 200ms from settings)

```python
buf = TokenChunkBuffer(seq_start=3)

# Feed tokens one at a time
chunk = buf.add("Hello")        # Returns None (below threshold)
chunk = buf.add(" " * 50)       # Returns PendingChunk(seq=3, content="Hello" + " "*50)

# Time-based flush (caller must invoke periodically)
chunk = buf.flush_if_stale()    # Returns PendingChunk if buffer is non-empty and >= flush_ms elapsed

# Final flush after stream ends
chunk = buf.flush_final()       # Returns PendingChunk with remaining buffer, or None
```

The buffer does NOT manage its own async timer. The caller (chat router) checks `flush_if_stale()` on each iteration of the stream loop and calls `flush_final()` after the stream completes.

**`PendingChunk` dataclass:** `seq: int`, `content: str`, `event_type: str = "token_chunk"`, `metadata: dict | None`.

### `EventSequencer`

Simple monotonic counter for assigning `seq` values across all event types within one message generation.

```python
seq = EventSequencer(start=1)
s1 = seq.next()  # 1
s2 = seq.next()  # 2
```

Separate from `TokenChunkBuffer`'s internal seq tracking. The `TokenChunkBuffer` has its own `_seq`, but in the chat router, the `EventSequencer` is used as the single source of truth for seq assignment, and the `TokenChunkBuffer`'s seq is not used for persistence.

### `constants.py`

```python
EVENT_STARTED = "started"
EVENT_DONE = "done"
EVENT_ERROR = "error"
EVENT_TOKEN_CHUNK = "token_chunk"
EVENT_REASONING_TOKEN = "reasoning_token"
EVENT_THINKING = "thinking"
```

No CHECK constraint on `chat_message_events.event_type` -- these are conventions only. New event types can be added without DDL changes.

---

## 4.8 Database Session (`src/api/db/models/session.py`)

```python
engine = create_async_engine(
    settings.db_url,           # e.g. "postgresql+asyncpg://user:password@db:5432/otis"
    echo=False,                # Set to True for SQL logging (was True in earlier development)
    future=True,
    pool_pre_ping=True,        # Validates connections before use (handles stale pool connections)
)

async_session_maker = sessionmaker(
    bind=engine,
    expire_on_commit=False,    # Objects remain usable after commit without re-query
    class_=AsyncSession,
)

async def get_db():            # FastAPI dependency
    async with async_session_maker() as session:
        yield session
```

**Connection URL format:** Must use `postgresql+asyncpg://` for the async engine. The `Settings.checkpoint_db_url` property strips `+asyncpg` for the sync psycopg driver used by LangGraph's checkpointer.

---

## 4.9 Services (`src/services/`)

### 4.9.1 `embedding_service.py` -- DEPRECATED

**Status:** Legacy module, superseded by `src/tasks/embedding_tasks.py`.

This module contains hardcoded connection strings, module-level `PGVector` instances, and a `pymupdf4llm`-based PDF extraction pipeline. It is imported only by the deprecated `src/agents/utils/nodes.py` and the `__main__` block at the bottom of the file. Do not use for new development.

**Chunk settings in this legacy module:**

- `chunk_size=800`, `chunk_overlap=100` (RecursiveCharacterTextSplitter)
- Headers: `#`, `##`, `###` (MarkdownHeaderTextSplitter)
- Embedding model: `nomic-embed-text` via Ollama

### 4.9.2 `concept_service.py` (312 lines)

Synchronous service called from the RQ embedding worker. Three main functions:

#### `extract_concepts(markdown_text, doc_name?) -> List[Dict[str, str]]`

- **Model:** `ChatOpenAI` with model `gpt-4.1-nano` (configurable via `CONCEPT_LLM_DEPLOYMENT` env).
- **Temperature:** 0.0
- **Max tokens:** 1000
- **Structured output:** `ExtractedConcepts` Pydantic model (list of `{name, summary}`).
- **Truncation:** Input markdown is truncated to 200,000 chars (~50k tokens).
- **Failure behavior:** Returns empty list `[]`. Logs exception. Non-fatal.
- **Output:** 3-10 concepts per document, each with a short name (2-5 words) and one-sentence summary (max 15 words).

#### `classify_chunks_to_concepts(chunks, concepts) -> List[Document]`

- **Model:** Same `gpt-4.1-nano`.
- **Structured output:** `ChunkConceptMappings` (list of `{chunk_index, concept_names}`).
- **Budget:** Each chunk is truncated to 500 chars for the prompt. Total classified text capped at `_CLASSIFY_CHUNK_CHAR_LIMIT = 120,000` chars.
- **Behavior:** Modifies `chunk.metadata["concepts"]` in-place. Chunks beyond the classified window get all concept names. Unmatched chunks get `["general"]`.
- **Failure behavior:** Tags all chunks as `["general"]`. Logs exception. Non-fatal.

#### `store_concepts(document_id, concepts, embedding_model, db, extractor_version?) -> None`

- **Embedding:** Batch-embeds all concept summaries using the provided model (same `nomic-embed-text` used for chunks).
- **Persistence:** Upserts into `document_concepts` using PostgreSQL `ON CONFLICT DO UPDATE` on the `(document_id, concept_name)` unique constraint. Updates `concept_summary`, `concept_embedding`, and `extractor_version` on conflict.
- **Failure behavior:** Rolls back transaction. Logs exception. Non-fatal.

### 4.9.3 `retrieval_service.py` (321 lines)

Implements two-layer concept-aware retrieval for the chat endpoint.

#### Configuration Constants

```python
CONCEPT_TOP_K = 3              # Max concepts from Layer 1
CONCEPT_SCORE_THRESHOLD = 0.3  # Minimum cosine similarity for concept match
MAX_CHUNKS = settings.max_retrieved_chunks  # Default: 20
```

#### Layer 1 -- Concept Matching (`_match_concepts`)

```python
async def _match_concepts(
    query_embedding: List[float],
    doc_ids: List[uuid.UUID],
    db: AsyncSession,
    top_k: int = 3,
    threshold: float = 0.3,
) -> List[Dict[str, Any]]  # [{concept_name, concept_summary, score}]
```

- Runs raw SQL against `document_concepts` table.
- Computes cosine similarity: `1 - (concept_embedding <=> query_vec::vector)`.
- Filters by `document_id IN (doc_ids)` and `concept_embedding IS NOT NULL`.
- Returns only concepts with `score >= threshold`.
- If no concepts match, retrieval falls back to Layer 2 without concept augmentation.

#### Layer 2 -- Chunk Retrieval (`_retrieve_chunks_sync`)

```python
def _retrieve_chunks_sync(
    query: str,
    doc_ids: List[uuid.UUID],
    concept_summaries: Optional[List[str]],
    collection_name: str,
    embedding_model: Any,
    k: int = 20,
) -> List[Document]
```

- Creates a `PGVector` instance per call (no connection pooling at this level).
- **Metadata filter:** `{"document_id": {"$in": [str(doc_id) for doc_id in doc_ids]}}`.
- **Query augmentation:** If concept summaries are available from Layer 1, appends them to the query: `"{query}\n\nRelevant topics: {summaries joined by '; '}"`.
- Runs in a thread executor from the async context via `loop.run_in_executor()`.
- **Retrieval strategy:** Default PGVector similarity search (not MMR). `k = MAX_CHUNKS`.

#### Deduplication (`_deduplicate_chunks`)

Uses first 200 characters of `page_content` as the dedup key. Preserves order (highest-ranked first). Caps at `MAX_CHUNKS`.

#### Public API

```python
async def retrieve_with_concepts(
    query: str,
    doc_ids: List[uuid.UUID],
    user_id: str,
    db: AsyncSession,
    embedding_model: Any,
) -> List[Document]
```

Full pipeline: embed query -> match concepts -> retrieve chunks -> deduplicate. Returns empty list on any unrecoverable error.

```python
def format_retrieved_context(docs: List[Document]) -> str
```

Formats chunks as `--- Source: {filename} (chunk {i}) ---\n{content}`, joined by double newlines.

### 4.9.4 `file_handling.py` (163 lines)

| Function        | Signature                                          | Notes                                                                                                                                                                                                  |
| --------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `store_file`    | `(files: List[UploadFile]) -> List[DocBase]`       | Streams each file to staging dir (`UPLOAD_DIR/.staging/`). Computes SHA-256 hash from disk. Never loads full file into RAM. Rejects disallowed extensions (400) and oversized files (400, limit: 10MB) |
| `delete_file`   | `(filename: str) -> bool`                          | Raises `HTTPException(404)` if file doesn't exist. Returns `True` on success                                                                                                                           |
| `download_file` | `(filename: str) -> FileResponse`                  | Raises `HTTPException(404)` if missing. Sets `media_type` based on extension                                                                                                                           |
| `zip_files`     | `(filenames: List[str]) -> StreamingResponse`      | Creates in-memory zip. **WARNING:** Loads entire zip into RAM via `io.BytesIO`. For many large files, this will exhaust memory                                                                         |
| `pdf_thumbnail` | `(pdf_path: str, size: int = 512) -> FileResponse` | Renders first page at 2x zoom using PyMuPDF, crops to square from top, resizes to `size x size`. Saves to `THUMBNAIL_DIR`. Returns cached PNG on subsequent calls (by filename, not content hash)      |

**Allowed extensions:**

```python
ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "md": "text/markdown",
}
```

**Environment variables:** `UPLOAD_DIR` (default: `/app/uploads`), `THUMBNAIL_DIR` (default: `/app/thumbnails`).

---

## 4.10 Background Tasks (`src/tasks/`)

### `embedding_tasks.py` -- `process_user_embeddings()`

```python
def process_user_embeddings(
    user_id: str,
    collection_name: str,
    document_ids: List[str],
    file_paths: List[str],
) -> dict
```

Full embedding pipeline, running synchronously in an RQ worker process.

**Pipeline steps:**

1. **DB setup:** Creates a sync SQLAlchemy engine from `DATABASE_URL` env var, stripping `+asyncpg` and `+psycopg` for `psycopg2` compatibility.
2. **Vectorstore record:** Gets or creates `UserVectorstore` row, sets `status="processing"`.
3. **Per-document loop:**
   - a. Fetches `Documents` row. Skips if `is_embedded=True` or `status="ready"` (idempotency).
   - b. **PDF extraction:** `pymupdf4llm.to_markdown(file_path)` converts PDF to markdown.
   - c. **Content hash:** Computes `compute_content_hash(md)` and stores in `document.content_hash`.
   - d. **Content-level dedup:** Checks for existing document with same `content_hash` and `is_embedded=True`. If found, sets `canonical_document_id` to the existing doc, marks current as `ready`/`is_embedded=True`, and skips embedding.
   - e. **Concept extraction:** Calls `extract_concepts(md, doc_name)` (non-fatal).
   - f. **Chunking:** MarkdownHeaderTextSplitter (headers: `#`, `##`, `###`) then RecursiveCharacterTextSplitter for chunks > 800 chars (`chunk_size=800`, `chunk_overlap=100`).
   - g. **Metadata:** Each chunk gets `{"user_id", "document_id", "source", "file_name"}`.
   - h. Stashes concepts in `process_user_embeddings._concept_buffer` dict (see anti-pattern note).
4. **Embedding:** Creates `PGVector` instance with `nomic-embed-text` via Ollama (`OLLAMA_BASE_URL` env). Calls `vector_store.add_documents(docling_docs)` for all chunks in one batch.
5. **Concept storage:** For each processed document with concepts, calls `store_concepts()` to persist concept embeddings.
6. **Finalization:** Marks all processed docs as `is_embedded=True`, `status="ready"`, `embedded_at=now()`. Updates `UserVectorstore` with `collection_id`, `document_count`, `status="ready"`.
7. **Error handling:** On failure, sets `UserVectorstore.status="failed"` and `error_message=str(e)`. Per-document failures are caught individually -- the loop continues with remaining documents.

**Chunking strategy:**

| Parameter        | Value                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------- |
| Splitter 1       | MarkdownHeaderTextSplitter (headers: `#`, `##`, `###`, strip_headers=False)              |
| Splitter 2       | RecursiveCharacterTextSplitter (chunk_size=800, chunk_overlap=100, add_start_index=True) |
| Trigger          | Splitter 2 only applied to chunks > 800 characters                                       |
| Embedding model  | `nomic-embed-text` (768 dimensions) via `OllamaEmbeddings`                               |
| Embedding target | `OLLAMA_BASE_URL` env (default: `http://ollama:11434`)                                   |
| Vector store     | `PGVector` with `REDIS_DATABASE_URL` env (sync psycopg driver)                           |

**Anti-pattern: `_concept_buffer` function attribute.**

```python
if not hasattr(process_user_embeddings, "_concept_buffer"):
    process_user_embeddings._concept_buffer = {}
```

Concepts are stashed as a function-level attribute on `process_user_embeddings` during the per-document loop, then read after embedding completes. This works because RQ executes tasks sequentially in a single process, but it is fragile:

- Concurrent workers would share the function object and corrupt each other's buffers.
- If the function is called recursively or from tests, state leaks between calls.
- The buffer is cleaned up with `del process_user_embeddings._concept_buffer` in the happy path, but not in all error paths.

### `worker.py` (15 lines)

```python
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

if __name__ == "__main__":
    worker = Worker(
        [Queue("default", connection=redis_conn)],
        connection=redis_conn,
    )
    worker.work()
```

Listens on the `default` queue. Run with `python -m src.worker` or `uv run -m src.worker`.

---

## 4.11 Agent Graph Builders (`src/agents/`)

### 4.11.1 `chat_agent.py` -- Active Chat Graph

**`create_chat_builder() -> StateGraph`**

Builds the main chat/MCQ generation graph. The topology:

```text
START
  |
  v
scope_classifier ──BLOCK──> END
  |
  ALLOW
  |
  v
intent_classifier
  |── PLAN ──> planner ──GENERATE──> retrieval -> require_retrieved_chunks
  |                     └─PATCH──> chat_tools                |
  |── TOOLS ──> chat_tools                     HAVE_CHUNKS ──> dispatch_questions
  |── CHAT ──> chat_model ──> END              NO_CHUNKS ──> chat_model
  |                                                          |
  |                                          question_subgraph_runner (fan-out via Send)
  |                                                          |
  |                                          assemble_final_output
  |                                                          |
  |                                          finalize_metadata
  |                                                          |
  v                                                     chat_model ──> END
chat_tools ──BUMP──> finalize_metadata
           └─CHAT──> chat_model
```

**Node registration:**

| Node Key                   | Function                        | Module                                              |
| -------------------------- | ------------------------------- | --------------------------------------------------- |
| `scope_classifier`         | `scope_classifier_graph_node`   | Wraps `scope_classifier_node` with `guardrail_llm`  |
| `intent_classifier`        | `intent_classifier_graph_node`  | Wraps `intent_classifier_node` with `intent_llm`    |
| `planner`                  | `planner_graph_node`            | Wraps `planner_node` with `planner_llm`             |
| `retrieval`                | `retrieval_node`                | Direct (no LLM wrapper)                             |
| `require_retrieved_chunks` | `require_retrieved_chunks_node` | Returns error message if no chunks                  |
| `dispatch_questions`       | `dispatch_questions_node`       | No-op (triggers fan-out via conditional edges)      |
| `question_subgraph_runner` | `question_subgraph_runner_node` | Invokes compiled `question_subgraph`                |
| `assemble_final_output`    | `assemble_final_mcqs_node`      | Output assembly                                     |
| `finalize_metadata`        | `finalize_metadata_node`        | Artifact version bump                               |
| `chat_model`               | `chat_model_graph_node`         | Wraps `chat_no_tools_node` with `chat_no_tools_llm` |
| `chat_tools`               | `chat_with_tools_node`          | Stub implementation                                 |

**Edge conditions:**

| Router                   | Condition                                       | Destinations                                                                                                       |
| ------------------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `route_scope`            | `state["before_agent_guardrail"].intent`        | `ALLOW` -> intent_classifier, `BLOCK` -> END                                                                       |
| `route_intent`           | `state["intent"].intent`                        | `mcq_request`/`followup` -> PLAN, `utility_task` -> TOOLS, `clarification` -> CHAT                                 |
| `route_after_planner`    | `state["edit_mode"]` + `state["edit_strategy"]` | `patch` -> PATCH (chat_tools), else -> GENERATE (retrieval)                                                        |
| `question_fanout_router` | `state["plan"].num_questions`                   | Returns `List[Send()]`, one per question index. In edit mode with targeted indices, only fans out to those indices |
| `route_after_tools`      | `state["artifact_bump"]`                        | `True` -> BUMP (finalize), `False` -> CHAT                                                                         |
| `route_retrieval_gate`   | `len(state["retrieved_chunks"])`                | >0 -> HAVE_CHUNKS, 0 -> NO_CHUNKS (falls through to chat_model)                                                    |

**Module-level compilation:**

```python
chat_builder = create_chat_builder()
```

The `StateGraph` instance is created at import time. It is compiled with a checkpointer in the FastAPI lifespan:

```python
app.state.compiled_chat_graph = chat_builder.compile(checkpointer=checkpointer)
```

### 4.11.2 `mcq_subgraph.py` -- Per-Question Subgraph

**`build_question_subgraph() -> CompiledGraph`**

Topology:

```text
START -> stem_generator -> options_generator -> validator
                                                 |
                                          PASS -> finalize_draft -> END
                                          RETRY -> stem_generator (loop)
                                          FAIL -> finalize_draft -> END
```

- **Max retries:** `_SUBGRAPH_MAX_RETRIES = 2`
- **Retry loop:** On validation failure, increments `retry_count` and loops back to `stem_generator`. After 2 retries, finalizes the draft regardless (FAIL path).
- **Fan-out:** The parent graph uses `Send()` to invoke this subgraph in parallel for each question index. Results are collected via the `mcq_drafts: Annotated[List[MCQDraft], add]` reducer.
- **Compiled at import time:** `question_subgraph = build_question_subgraph()` -- no checkpointer (stateless).

### 4.11.3 `graph.py` -- DEPRECATED

```text
START -> fetch_documents -> generate_summaries -> human_approval
      -> generate_search_queries -> retrieve_context -> END
```

- Uses `AgentNodes` class from `src/agents/utils/nodes.py`.
- `human_approval` triggers a LangGraph `interrupt()` for human-in-the-loop concept selection.
- Model: `gpt-4o-mini` (Azure, temperature=0.2).
- **Status:** Superseded by `chat_agent.py` + `retrieval_service.py`. Kept for the `/v1/graph/start` and `/v1/graph/resume` endpoints.

### 4.11.4 `utils/helpers.py` -- Prompt Context Helpers

| Function                  | Signature         | Notes                                                                                          |
| ------------------------- | ----------------- | ---------------------------------------------------------------------------------------------- |
| `build_retrieved_context` | `(chunks) -> str` | Formats agent-retrieved chunks into prompt-ready context text for generation/validation nodes. |

---

## 4.12 Agent Nodes (`src/agents/nodes/`)

### `scope.py` -- `scope_classifier_node(state, guardrail_llm) -> dict`

- **Input:** `state["messages"]` (last message content)
- **Output:** `{"before_agent_guardrail": ScopeClassification(intent="ALLOW"|"BLOCK")}`
- **Model:** `guardrail_llm` (gpt-4.1-nano)
- **Prompt:** `PROMPT_REGISTRY["scope_classifier"]` -- variables: `{user_request}`
- **Structured output:** `ScopeClassification` (Pydantic: `intent: Literal["ALLOW", "BLOCK"]`)
- **SSE events:** Emits `node_update` via `get_stream_writer()` (started + completed)
- **Failure:** If LLM fails to parse structured output, raises. No fallback.

### `intent.py` -- `intent_classifier_node(state, intent_llm) -> dict`

- **Input:** `state["messages"]` (last message content)
- **Output:** `{"intent": IntentResult(intent=...)}`
- **Model:** `intent_llm` (gpt-4.1-nano)
- **Prompt:** `PROMPT_REGISTRY["intent_classifier"]` -- variables: `{session_summary, user_message}`
- **Structured output:** `IntentResult` (Pydantic: `intent: Literal["mcq_request", "followup", "utility_task", "clarification"]`)
- **SSE events:** started + completed (detail = intent class)
- **Failure:** No fallback. Structured output parse failure propagates.

### `planner.py` -- `planner_node(state, planner_llm) -> dict`

- **Input:** `state["messages"]`, `state["plan"]` (previous plan), `state["validation_feedback"]`
- **Output:** `{"plan": PlannerOutput, "plan_version": int, "edit_mode": bool, "edit_target": str, "edit_indices": List[int], "edit_strategy": str}`
- **Model:** `planner_llm` (gpt-4.1-nano)
- **Prompt:** `PROMPT_REGISTRY["planner"]` -- variables: `{user_message, session_summary, previous_plan, validation_feedback}`
- **Structured output:** `PlannerOutput` (extends `TestGenerationPlan` + `edit_mode`, `edit_target`, `edit_indices`, `edit_strategy`)
- **Edit expansion:** If `edit_target == "all"`, `edit_indices` is expanded to `list(range(num_questions))`.
- **SSE events:** started + completed (detail = question count)

### `retrieval.py` -- `retrieval_node(state) -> dict`

- **Input:** `state["doc_ids"]`, `state["plan"].retrieval_queries`, `state["user_id"]`
- **Output:** `{"retrieved_chunks": List[RetrievedChunk], "retrieval_status": RetrievalStatus}`
- **Model:** None (uses PGVector directly via `src/agents/utils/services/retrieval.retrieve_chunks`)
- **Fallback query:** If no retrieval queries from planner, uses `user_prompt` or `plan.topic` or `"mcq generation"`.
- **Failure behavior:** Returns `retrieved_chunks=[]`, `retrieval_status=RetrievalStatus(status="failed", error=str(exc))`. Does NOT raise. Graph continues to `require_retrieved_chunks` which routes to chat_model if no chunks.
- **Missing doc_ids:** Returns failure status, does not raise.
- **Missing user_id:** Returns failure status, does not raise.

### `chat.py` -- `chat_no_tools_node(state, chat_llm) -> dict`

- **Input:** `state["messages"]`, `state["final_mcqs"]`, `state["tool_result"]`
- **Output:** `{"messages": [AIMessage]}`
- **Model:** `chat_no_tools_llm` (gpt-4.1-nano, streaming=True)
- **Prompt:** `PROMPT_REGISTRY["chat_no_tools"]` -- variables: `{session_summary, final_mcqs, user_message}`
- **Behavior:** Formats final MCQs into display text, concatenates with tool_result, invokes LLM. The response is streamed via LangGraph's message stream mode.

### `chat.py` -- `chat_with_tools_node(state) -> dict` (STUB)

- **Input:** `state["edit_strategy"]`, `state["edit_indices"]`, `state["edit_mode"]`
- **Output:** `{"tool_result": str, "artifact_bump": bool}`
- **Behavior:** Returns a placeholder JSON string. The `patch_mcq` tool route is scaffolded but NOT implemented. Returns `artifact_bump=True` only if `edit_mode` is True and strategy is "patch".

### `output.py` -- `assemble_final_mcqs_node(state) -> dict`

- **Input:** `state["mcq_drafts"]` (accumulated from subgraph Send fan-out)
- **Output:** `{"final_mcqs": List[FinalMCQ]}`
- **Behavior:** Sorts drafts by `question_index`. Maps options to `MCQOption(key="A"|"B"|"C"|"D", text=...)`. Defaults `right_answer` to `"A"` if `draft.answer` is None.

### `output.py` -- `finalize_metadata_node(state) -> dict`

- **Input:** `state["mcq_drafts"]`, `state["artifact_bump"]`, `state["artifact_version"]`
- **Output:** `{"artifact_version": int}` or `{}`
- **Behavior:** Bumps `artifact_version` by 1 if there are new drafts or `artifact_bump` is True.

### `validator.py` -- `validator_node(state, validator_llm) -> dict`

- **Input:** `state["stem"]`, `state["options"]`, `state["correct_answer"]`, `state["plan"]`, `state["retrieved_chunks"]`
- **Output:** `{"validation_passed": bool, "validation_feedback": str, "retry_count": int}`
- **Model:** `validator_llm` (gpt-4.1-nano)
- **Prompt:** `PROMPT_REGISTRY["validator"]` -- variables: `{plan, draft, retrieved_context}`
- **Structured output:** `ValidatorOutput` (extends `ValidationResult`)
- **Validation criteria:** Stem clarity, distractor plausibility, single correct answer, Bloom's alignment, factual grounding against retrieved context. Does NOT evaluate explanation quality.
- **Retry logic:** Increments `retry_count` on failure. The subgraph routes back to `stem_generator` if `retry_count < _SUBGRAPH_MAX_RETRIES` (2).

### `generation/stem.py` -- `stem_generator_node(state, stem_llm) -> dict`

- **Input:** `state["question_index"]`, `state["plan"]`, `state["retrieved_chunks"]`
- **Output:** `{"stem": str}`
- **Model:** `stem_llm` (gpt-4.1-nano)
- **Prompt:** `PROMPT_REGISTRY["stem_generation"]` -- variables: `{question_index, plan, retrieved_context}`
- **Output format:** Raw text (not structured output). The LLM response content is stripped and returned as a string.

### `generation/options.py` -- `options_generator_node(state, options_llm) -> dict`

- **Input:** `state["question_index"]`, `state["plan"]`, `state["stem"]`
- **Output:** `{"options": List[str], "correct_answer": Literal["A","B","C","D"], "explanation": str}`
- **Model:** `options_llm` (gpt-4.1-nano)
- **Prompt:** `PROMPT_REGISTRY["options_generation"]` -- variables: `{plan, stem, distractor_strategy}`
- **Structured output:** `OptionsOutput` (Pydantic: `options: List[str]` (exactly 4), `correct_answer`, `explanation`)

### `generation/finalize.py` -- DEAD CODE

Defines `finalize_draft_node()` but it is NOT used by `mcq_subgraph.py`. The subgraph defines its own inline `_finalize_draft_node()` function. This file is dead code.

---

## 4.13 Agent State & Schemas

### `src/agents/utils/state.py`

**Top-level state (`State`):**

```python
class State(TypedDict, total=False):
    # Guardrails
    before_agent_guardrail: BeforeAgentGuardrail
    intent: IntentClassification

    # Conversation
    messages: Annotated[List[ChatMessage], add]   # Reducer: list append
    user_prompt: str
    user_id: str
    doc_ids: List[uuid.UUID]

    # Retrieval
    search_queries: List[str]
    retrieved_chunks: List[RetrievedChunk]
    retrieval_status: RetrievalStatus
    use_naive_generator: bool

    # Planning
    plan: TestGenerationPlan
    plan_version: int
    retry_count: int
    max_retries: int
    validation_feedback: str

    # MCQ Generation
    mcq_question_prompts: List[str]
    mcq_drafts: Annotated[List[MCQDraft], add]    # Reducer: list append
    final_mcqs: List[FinalMCQ]

    # Edit Mode
    edit_mode: bool
    edit_target: Literal["all", "specific"]
    edit_indices: List[int]
    edit_strategy: Literal["regenerate", "patch"]
    existing_drafts: List[MCQDraft]

    # Artifact Versioning
    artifact_version: int
    retrieval_signature: Optional[str]
    retrieval_signature_valid: bool
    artifact_bump: bool
    tool_result: str
```

**Reducers:** Two fields use the `add` operator as a reducer:

- `messages: Annotated[List[ChatMessage], add]` -- new messages are appended to existing list.
- `mcq_drafts: Annotated[List[MCQDraft], add]` -- drafts from parallel subgraph invocations are merged.

All other fields use default replacement semantics (last write wins).

**Question subgraph state (`QuestionSubgraphState`):**

```python
class QuestionSubgraphState(TypedDict, total=False):
    plan: TestGenerationPlan
    question_index: int
    retrieved_chunks: List[RetrievedChunk]
    existing_draft: Optional[MCQDraft]
    stem: Optional[str]
    options: Optional[List[str]]
    correct_answer: Optional[str]
    explanation: Optional[str]
    retry_count: int
    validation_passed: bool
    validation_feedback: str
    draft: Optional[MCQDraft]
```

**Legacy state (`AgentState`):**

```python
class AgentState(TypedDict, total=False):
    chat_message: Annotated[List[ChatMessage], add]
    doc_ids: List[uuid.UUID]
    collection_name: Optional[List[str]]
    documents: Optional[List[DocumentContent]]
    overview: Optional[List[Overview]]
    user_prompt: Optional[List[str]]
    retrived_context: List                      # Typo: "retrived" (sic)
    selected_concepts: List[Concept]
    search_queries: List[SearchQueries]
```

Used only by the deprecated `graph.py`.

### `src/agents/nodes/schemas.py`

| Schema                | Base                 | Fields                                                                              | Used By                 |
| --------------------- | -------------------- | ----------------------------------------------------------------------------------- | ----------------------- |
| `ScopeClassification` | `BaseModel`          | `intent: Literal["ALLOW", "BLOCK"]`                                                 | `scope.py`              |
| `IntentResult`        | `BaseModel`          | `intent: Literal["mcq_request", "followup", "utility_task", "clarification"]`       | `intent.py`             |
| `PlannerOutput`       | `TestGenerationPlan` | + `edit_mode`, `edit_target`, `edit_indices`, `edit_strategy`                       | `planner.py`            |
| `OptionsOutput`       | `BaseModel`          | `options: List[str]` (4), `correct_answer: Literal["A","B","C","D"]`, `explanation` | `generation/options.py` |
| `ValidatorOutput`     | `ValidationResult`   | Inherits `validation_passed`, `validation_feedback`, `validation_score`             | `validator.py`          |

---

## 4.14 Agent Prompts (`src/agents/prompts/`)

### Prompt Registry

```python
PROMPT_REGISTRY = {
    "scope_classifier":   scope_classifier_prompt,
    "intent_classifier":  intent_classifier_prompt,
    "planner":            planner_prompt,
    "stem_generation":    stem_generation_prompt,
    "options_generation": options_generation_prompt,
    "validator":          validator_prompt,
    "chat_no_tools":      chat_no_tools_prompt,
}
```

All prompts are `langchain_core.prompts.PromptTemplate` instances created with `PromptTemplate.from_template()`. Nodes access prompts via `PROMPT_REGISTRY[key].ainvoke({...})`, which returns a formatted string.

The registry pattern decouples prompt text from node logic. To change a prompt, edit only the prompt module -- no node code changes required.

### Prompt Details

#### `scope_classifier` (`classification.py`)

- **Variables:** `{user_request}`
- **Logic:** ALLOW only for quiz/test/MCQ generation requests. BLOCK for general chat, unrelated questions, disallowed content. Default: BLOCK if unsure.

```text
Classify the user input.
ALLOW only if the user is requesting quiz, test, or MCQ generation.
BLOCK if user is chatting generally, asking unrelated questions, or requesting disallowed content.
If unsure, output BLOCK.
Input: {user_request}
Output: ALLOW or BLOCK
```

**Architecture tension (requires code check):** This strict prompt text conflicts with graph routes that support `clarification -> chat_model` and `utility_task -> chat_tools`. Verify whether runtime behavior relaxes these rules or whether those routes are effectively unreachable.

#### `intent_classifier` (`classification.py`)

- **Variables:** `{session_summary, user_message}`
- **Classes:** `mcq_request`, `followup`, `utility_task`, `clarification`
- **Note:** `session_summary` is currently always passed as empty string `""`.

```text
You are an intent classifier for an MCQ assistant.
Classify the user input into exactly one of:
- mcq_request
- followup
- utility_task
- clarification
Use the provided session summary for context.
Session summary: {session_summary}
User message: {user_message}
Return only the class label.
```

#### `planner` (`planner.py`)

- **Variables:** `{user_message, session_summary, previous_plan, validation_feedback}`
- **Output fields:** topic, difficulty, num_questions, blooms_level, stem_guidance, distractor_strategy, retrieval_queries, concepts

```text
Create an MCQ generation plan from the user request.
User message: {user_message}
Session summary: {session_summary}
Previous plan (if any): {previous_plan}
Validation feedback (if any): {validation_feedback}
Return a plan with:
- topic
- difficulty (EASY|MEDIUM|HARD)
- num_questions
- blooms_level (REMEMBER|UNDERSTAND|APPLY|ANALYZE|EVALUATE|CREATE)
- stem_guidance
- distractor_strategy
- retrieval_queries
- concepts
```

#### `stem_generation` (`generation.py`)

- **Variables:** `{question_index, plan, retrieved_context}`
- **Output:** Raw text (question stem only)

```text
Generate one MCQ question stem for question index {question_index}.
Plan: {plan}
Retrieved context: {retrieved_context}
Return only the question stem text.
```

#### `options_generation` (`generation.py`)

- **Variables:** `{plan, stem, distractor_strategy}`
- **Output:** Structured JSON (options, correct_answer, explanation)
- **Constraints:** Exactly 4 options, exactly 1 correct, balanced lengths, no near-duplicates

#### `validator` (`validator.py`)

- **Variables:** `{plan, draft, retrieved_context}`
- **Output:** Structured JSON (validation_passed, validation_score, validation_feedback)
- **Checks:** Stem clarity, distractor plausibility, single correct answer, Bloom's alignment, factual grounding. Explicitly does NOT evaluate explanation quality.

#### `chat_no_tools` (`chat.py`)

- **Variables:** `{session_summary, final_mcqs, user_message}`
- **Behavior:** If final MCQs exist, presents them with explanations. Otherwise, answers as a normal clarification.

```text
You are a concise MCQ assistant.
Session summary: {session_summary}
Final MCQs: {final_mcqs}
User message: {user_message}
If final MCQs exist, present them clearly including explanation for each correct answer.
If no final MCQs exist, answer as a normal clarification.
```

### Legacy Prompts (`src/agents/utils/prompts.py`)

A separate `PROMPTS` dict exists in `src/agents/utils/prompts.py` for the deprecated graph:

```python
PROMPTS = {
    "summarize":               summarize_prompt,
    "summarize2":              summarize_prompt2,
    "search_queries":          search_queries,
    "search_queries_v2":       summarize_prompt2,   # NOTE: maps to same prompt as summarize2
    "query_generation":        query_generation,
    "naive_mcq_generation":    naive_mcq_generation,
    "before_agent_guardrail":  before_agent_guardrail,
}
```

This is only used by `src/agents/utils/nodes.py` (the legacy `AgentNodes` class).

---

## Things a First-Time Contributor Would Likely Misunderstand

1. **Two model files, one is dead.** The root `models.py` looks authoritative (it includes LangGraph checkpoint tables) but it is NOT imported by any active code. The canonical models are in `src/api/db/models/__init__.py`. Editing `models.py` will have no effect on the running application. The LangGraph checkpoint tables are created by `AsyncPostgresSaver.setup()` at startup, not by SQLAlchemy's `Base.metadata.create_all()`.

2. **Two prompt registries exist.** `src/agents/prompts/__init__.py` → `PROMPT_REGISTRY` is used by the active chat graph nodes. `src/agents/utils/prompts.py` → `PROMPTS` is used by the deprecated `AgentNodes` class. Editing the wrong one will not affect the active graph. The key names also differ (e.g., `"scope_classifier"` vs `"before_agent_guardrail"`).

3. **The embedding worker is synchronous, the API is async.** `src/tasks/embedding_tasks.py` uses a sync `Session` and sync `PGVector`. Importing async code (like `async_session_maker`) or awaiting coroutines inside the worker will fail silently or raise. The database URL must be converted from `+asyncpg` to a sync driver. This conversion happens in the task function itself, not in the config layer.
