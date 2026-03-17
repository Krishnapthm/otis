---
applyTo: "src/api/**,src/core/**,src/services/**,src/tasks/**,src/workers/**,src/worker.py,src/file_handling.py"
---

# FastAPI Backend — canonical patterns

> These rules apply to every file under `src/api/`, `src/core/`, `src/services/`,
> `src/tasks/`, and `src/workers/`. They complement the cross-cutting rules in
> `.github/copilot-instructions.md`.

## Separation of concerns

Each layer has a single job. Never mix responsibilities across layers.

| Layer     | Location               | Responsibility                                |
| --------- | ---------------------- | --------------------------------------------- |
| Routers   | `src/api/v1/routers/`  | Input validation, DI wiring, response shaping |
| CRUD      | `src/api/crud/`        | Data access via ORM — no business logic       |
| Services  | `src/services/`        | Business logic — no HTTP, no DB sessions      |
| Schemas   | `src/api/db/schema.py` | All Pydantic request/response models          |
| Config    | `src/core/config.py`   | All env var access via `Settings` singleton   |
| Security  | `src/core/security.py` | Auth helpers, token logic                     |
| Utilities | `src/api/utils/`       | Reusable helpers shared across routers/CRUD   |

**Router handlers must not contain business logic or DB queries.** Delegate to
services and CRUD functions respectively.

## Dependency injection

Always inject dependencies — never instantiate them inline inside handlers.

```python
# ✅ correct — DI via Depends
@router.get("/chats/{chat_id}")
async def get_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AuthResponse = Depends(get_current_user),
) -> ChatResponse:
    return await crud.get_chat(db, chat_id, current_user.id)

# ❌ wrong — inline instantiation
async def get_chat(chat_id: UUID):
    db = AsyncSession(engine)  # never do this
```

**DB sessions**: `Depends(get_db)` from `src/api/db/models/session.py`  
**Auth**: `Depends(get_current_user)` from `src/core/security.py`  
**Graph**: `Depends(get_graph)` / `Depends(get_chat_graph)` from the respective router

## Shared utilities — DRY

Extract any logic used in more than one CRUD or router file into `src/api/utils/`.

- **Ownership / admin checks** — do not repeat `if user.role != "admin": raise HTTPException(403)`
  inline in CRUD files. Use a shared guard from `src/api/utils/auth.py`
- **File handling** — single source of truth is `src/services/file_handling.py`.
  `src/file_handling.py` (root-level duplicate) is dead — delete on next touch
- **UPLOAD_DIR, THUMBNAIL_DIR** — must be read from `settings`, not via
  `os.environ.get("UPLOAD_DIR", "/app/uploads")` scattered across files

## Schemas

All Pydantic models live in `src/api/db/schema.py`. Naming convention:

```
{Resource}Create   → request body for POST
{Resource}Update   → request body for PATCH/PUT
{Resource}Response → response model
```

Never define ad-hoc Pydantic models inside router files.

## Config — no raw os.getenv()

All env vars flow through the `settings` singleton from `src/core/config.py`.
If a variable is missing from `Settings`, add it there — do not reach for
`os.getenv()` with a hardcoded fallback.

```python
from src.core.config import settings

upload_dir = settings.upload_dir          # ✅
os.environ.get("UPLOAD_DIR", "/uploads") # ❌
```

Variables that **must** be added to `Settings` (currently scattered as raw
`os.getenv()` calls): `UPLOAD_DIR`, `THUMBNAIL_DIR`, `OLLAMA_BASE_URL`,
`REDIS_URL`, `REDIS_DATABASE_URL`, `CONCEPT_LLM_DEPLOYMENT`.

## Database access

- SQLAlchemy **async ORM** via `Depends(get_db)` for all standard queries
- Raw `text()` SQL only for pgvector cosine-similarity queries
- Always **parameterized** — never f-string interpolation in SQL:

```python
# ✅ correct
stmt = text("SELECT ... WHERE id = ANY(:ids)").bindparams(ids=doc_ids)

# ❌ SQL injection risk
stmt = text(f"SELECT ... WHERE id IN ({', '.join(doc_id_literals)})")
```

- Use `fastapi.status` constants — never bare integer status codes in `HTTPException`

## Error handling

```python
from fastapi import HTTPException
from fastapi import status

# Simple error
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

# Structured domain error (follow the dedup pattern in src/api/crud/docs.py)
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={"type": "content_duplicate", "canonical_id": str(existing.id)},
)
```

- `RuntimeError` must never escape into HTTP handlers — catch and convert
- Bare `except:` is forbidden — always catch a specific exception type

## Logging

```python
import logging
logger = logging.getLogger(__name__)
```

No `print()`. No structlog. Module-level logger, named after the module.

## Timestamps

All DB timestamps must be **UTC** (`TIMESTAMPTZ`). Never store or convert to IST
(or any local timezone) in the backend. Timezone conversion belongs in the
frontend.

```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc)  # ✅
# ❌ IST = timezone(timedelta(hours=5, minutes=30))
```

## On-touch cleanup checklist

When you edit **any** file in these directories, also fix these in that same file:

- [ ] Replace `os.getenv(...)` / `os.environ.get(...)` → `settings.xxx`
      (add the field to `Settings` if it doesn't exist yet)
- [ ] Replace bare integer status codes → `fastapi.status` constants
- [ ] Replace `print(...)` → `logger.info/warning/error(...)`
- [ ] Add Google-style docstring to any touched public function or class
- [ ] Remove unused imports
- [ ] `src/core/security.py`: fix `plain_passowrd` → `plain_password`,
      `"acces denied"` → `"access denied"`
- [ ] `src/api/v1/routers/mcqs.py`: fix `"donwload mcq"` → `"download mcq"`
- [ ] `src/tasks/embedding_tasks.py`: replace all `print(...)` with `logger` calls;
      replace bare `except:` with `except Exception as exc:`
- [ ] `src/services/retrieval_service.py`: replace f-string doc ID interpolation
      with `bindparams` — SQL injection risk at L106
- [ ] `src/services/embedding_service.py`: remove hardcoded `user:password`
      connection string; remove `__main__` block with `print()` statements
- [ ] If touching `src/api/crud/projects.py`: remove hardcoded IST timezone,
      use `datetime.now(timezone.utc)` instead
- [ ] Dead files — delete on next touch:
      `src/api/routers/docs.py`, `src/api/routers/mcqs.py`, `src/file_handling.py`
