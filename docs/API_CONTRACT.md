# 7. API Contract

**TL;DR:** Otis exposes a FastAPI backend at `http://localhost:8000/v1` with JWT Bearer authentication. All mutations require a valid access token. Two distinct SSE streaming protocols exist: one for chat (newline-delimited `data:` JSON) and one for the agent graph (same framing, different event vocabulary).

---

## Assumptions

- The FastAPI app is served via Uvicorn on port 8000. No reverse proxy rewriting is assumed.
- All UUIDs are v4, serialized as lowercase hyphenated strings (`550e8400-e29b-41d4-a716-446655440000`).
- Timestamps are ISO 8601 with timezone (`2026-02-27T10:30:00.000000+00:00`).
- The JWT signing algorithm is HS256. The `sub` claim holds the user's email, not the user_id.
- `refresh_token` rotation is stored in Redis when available, falling back to an in-process dict (lost on restart).
- SSE streams use `text/event-stream` content type. The server does not send named SSE event fields (`event:`); all payloads are under bare `data:` lines.
- The login endpoint uses `OAuth2PasswordRequestForm` (form-encoded `username` + `password`), not JSON. The `username` field carries the email.
- Error responses from FastAPI follow the shape `{ "detail": "<string>" }` unless noted otherwise. Pydantic validation errors return `{ "detail": [{ "loc": [...], "msg": "...", "type": "..." }] }`.
- The agent graph (`/v1/graph/*`) is a deprecated RAG/concept-extraction pipeline kept for backward compatibility.

---

## 7.1 Base URL and Authentication

**Base URL:**

```text
http://localhost:8000/v1
```

All endpoints are mounted under `/v1` via `app.include_router(..., prefix="/v1")` in `src/api/v1/main.py`.

**Authentication scheme:** OAuth2 Bearer token.

```text
Authorization: Bearer <access_token>
```

**Token acquisition:** `POST /v1/auth/login` returns an access token and a refresh token. The access token is a JWT signed with HS256.

**JWT claims:**

| Claim | Type   | Description                     |
| ----- | ------ | ------------------------------- |
| `sub` | string | User's email address            |
| `typ` | string | `"access"` or `"refresh"`       |
| `jti` | string | Unique token ID (UUID v4)       |
| `exp` | int    | Expiration (Unix epoch seconds) |

**Token lifetimes:**

| Token type    | Default TTL |
| ------------- | ----------- |
| Access token  | 30 minutes  |
| Refresh token | 7 days      |

**CORS:** The server exposes `X-Thread-ID` response header and allows credentials from `http://localhost:3000` and `http://localhost:5173`.

---

## 7.2 Authentication Endpoints (`/v1/auth/`)

### POST `/v1/auth/register`

Create a new user account.

**Request body** (`application/json`):

```json
{
  "email": "user@example.com",
  "uname": "display_name",
  "password": "P@ssw0rd!"
}
```

**Password validation rules** (server-side, returns 422 on failure):

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (`string.punctuation`)

**Response** `201 Created`:

The response schema is determined by the `create_user` CRUD function return value. The router does not declare a `response_model`.

**Error responses:**

| Status | Detail                    | Cause                        |
| ------ | ------------------------- | ---------------------------- |
| 400    | `"email already exists"`  | Duplicate email registration |
| 422    | Pydantic validation array | Password rules violated      |

---

### POST `/v1/auth/login`

**Request body** (`application/x-www-form-urlencoded`):

```text
username=user@example.com&password=P@ssw0rd!
```

This endpoint uses FastAPI's `OAuth2PasswordRequestForm`. The field is named `username` per OAuth2 spec, but it carries the user's email.

**Response** `200 OK` (`Token`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error responses:**

| Status | Detail                               | Cause                              |
| ------ | ------------------------------------ | ---------------------------------- |
| 401    | `"Incorrect email or password"`      | Bad credentials                    |
| 500    | `"Failed to generate refresh token"` | Server-side token creation failure |

---

### GET `/v1/auth/me`

Return the authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response** `200 OK` (`AuthResponse`):

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "uname": "display_name",
  "email": "user@example.com",
  "role": "user"
}
```

`role` is one of `"admin"` or `"user"`.

**Error responses:**

| Status | Detail                  | Cause                           |
| ------ | ----------------------- | ------------------------------- |
| 401    | `"Invalid Credentials"` | Missing/expired/malformed token |

---

### POST `/v1/auth/logout`

Log out the current user. Revokes the stored refresh JTI.

**Headers:** `Authorization: Bearer <access_token>`

**Response** `200 OK`: Implementation-defined (returned by `logout_user` CRUD).

---

### POST `/v1/auth/refresh`

Rotate the access token using a refresh token.

**Request body** (`application/json`):

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response** `200 OK` (`Token`):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error responses:**

| Status | Detail                             | Cause                         |
| ------ | ---------------------------------- | ----------------------------- |
| 401    | `"Invalid refresh token"`          | Expired, revoked, or tampered |
| 500    | `"Failed to rotate refresh token"` | Server-side failure           |

**Important:** Each refresh token is single-use. After a successful refresh, the old refresh JTI is replaced. Replaying an old refresh token will fail with 401.

---

### DELETE `/v1/auth/delete`

Delete the authenticated user's account.

**Headers:** `Authorization: Bearer <access_token>`

**Response** `200 OK`: Implementation-defined.

**Error responses:**

| Status | Detail             | Cause       |
| ------ | ------------------ | ----------- |
| 404    | `"User not found"` | Stale token |

---

### PUT `/v1/auth/edit`

Update the authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Request body** (`application/json`): All fields optional.

```json
{
  "uname": "new_name",
  "email": "new@example.com",
  "password": "N3wP@ss!"
}
```

**Response** `200 OK` (`UserResponse`):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "uname": "new_name",
  "email": "new@example.com",
  "created_at": "2026-02-20T10:00:00+00:00"
}
```

**Error responses:**

| Status | Detail                   | Cause                       |
| ------ | ------------------------ | --------------------------- |
| 404    | `"User not found"`       | Stale token                 |
| 409    | `"Email already in use"` | Email taken by another user |

---

## 7.3 Chat Endpoints (`/v1/chats/`)

All chat endpoints require `Authorization: Bearer <access_token>`.

### POST `/v1/chats/`

Create a new chat session.

**Request body** (`ChatCreate`):

```json
{
  "title": "My study session"
}
```

`title` is optional and nullable.

**Response** `201 Created` (`ChatResponse`):

```json
{
  "chat_id": "a1b2c3d4-...",
  "user_id": "550e8400-...",
  "status": "active",
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "title": "My study session",
  "created_at": "2026-02-27T10:30:00+00:00",
  "updated_at": "2026-02-27T10:30:00+00:00",
  "last_message_at": null,
  "deleted_at": null
}
```

---

### GET `/v1/chats/`

List chats for the authenticated user.

**Query parameters:**

| Param         | Type   | Default | Description                                        |
| ------------- | ------ | ------- | -------------------------------------------------- |
| `limit`       | int    | 50      | Maximum number of chats to return                  |
| `skip`        | int    | 0       | Offset for pagination                              |
| `chat_status` | string | null    | Filter by status (`active`, `archived`, `deleted`) |

**Response** `200 OK`: `ChatResponse[]`

---

### GET `/v1/chats/{chat_id}`

Get a single chat by ID.

**Response** `200 OK`: `ChatResponse`

**Error responses:**

| Status | Detail                              | Cause                       |
| ------ | ----------------------------------- | --------------------------- |
| 404    | Chat not found or not owned by user | Invalid UUID or wrong owner |

---

### PATCH `/v1/chats/{chat_id}`

Update a chat's title or status.

**Request body** (`ChatUpdate`):

```json
{
  "title": "Renamed chat",
  "status": "archived"
}
```

Both fields are optional. `status` must be one of `"active"`, `"archived"`, `"deleted"`.

**Response** `200 OK`: `ChatResponse`

---

### DELETE `/v1/chats/{chat_id}`

Delete a chat.

**Response** `200 OK`:

```json
{
  "message": "Chat deleted"
}
```

---

### POST `/v1/chats/{chat_id}/messages`

Create a message in a chat (manual insertion, not via invoke).

**Request body** (`ChatMessageCreate`):

```json
{
  "role": "user",
  "content": "What is photosynthesis?",
  "doc_ids": ["doc-uuid-1"],
  "status": "completed"
}
```

| Field             | Type                                                        | Required | Default       |
| ----------------- | ----------------------------------------------------------- | -------- | ------------- |
| `role`            | `"user"` \| `"assistant"` \| `"tool"`                       | yes      |               |
| `content`         | string \| null                                              | no       | null          |
| `structured_data` | object \| null                                              | no       | null          |
| `doc_ids`         | UUID[] \| null                                              | no       | null          |
| `status`          | `"pending"` \| `"streaming"` \| `"completed"` \| `"failed"` | no       | `"completed"` |
| `input_tokens`    | int \| null                                                 | no       | null          |
| `output_tokens`   | int \| null                                                 | no       | null          |
| `error`           | object \| null                                              | no       | null          |

**Response** `201 Created` (`ChatMessageResponse`):

```json
{
  "message_id": "msg-uuid-...",
  "chat_id": "a1b2c3d4-...",
  "role": "user",
  "sequence": 1,
  "status": "completed",
  "content": "What is photosynthesis?",
  "structured_data": null,
  "doc_ids": ["doc-uuid-1"],
  "input_tokens": null,
  "output_tokens": null,
  "error": null,
  "created_at": "2026-02-27T10:31:00+00:00"
}
```

---

### GET `/v1/chats/{chat_id}/messages`

List messages in a chat, ordered by sequence.

**Query parameters:**

| Param   | Type | Default | Description  |
| ------- | ---- | ------- | ------------ |
| `limit` | int  | 200     | Max messages |
| `skip`  | int  | 0       | Offset       |

**Response** `200 OK`: `ChatMessageResponse[]`

---

### GET `/v1/chats/{chat_id}/messages/{message_id}`

Get a single message.

**Response** `200 OK`: `ChatMessageResponse`

---

### PATCH `/v1/chats/{chat_id}/messages/{message_id}`

Update a message's content, status, or metadata.

**Request body** (`ChatMessageUpdate`): Same fields as `ChatMessageCreate`, all optional.

**Response** `200 OK`: `ChatMessageResponse`

---

### DELETE `/v1/chats/{chat_id}/messages/{message_id}`

Delete a single message.

**Response** `200 OK`:

```json
{
  "message": "Message deleted"
}
```

---

### POST `/v1/chats/{chat_id}/invoke`

Send a user message and stream the assistant response via SSE.

This is the primary chat interaction endpoint. It creates both the user message and assistant message records, then streams the LLM response.

**Request body** (`ChatInvokeRequest`):

```json
{
  "message": "Explain the Krebs cycle",
  "doc_ids": ["doc-uuid-1", "doc-uuid-2"],
  "mentions": [
    { "id": "doc-uuid-1", "label": "biology.pdf", "triggerChar": "@" }
  ],
  "edit_mode": false,
  "edit_target": "all",
  "edit_indices": [],
  "edit_strategy": "regenerate"
}
```

| Field           | Type                        | Required | Default        |
| --------------- | --------------------------- | -------- | -------------- |
| `message`       | string                      | yes      |                |
| `doc_ids`       | UUID[] \| null              | no       | null           |
| `mentions`      | object[] \| null            | no       | null           |
| `edit_mode`     | bool                        | no       | false          |
| `edit_target`   | `"all"` \| `"specific"`     | no       | `"all"`        |
| `edit_indices`  | int[]                       | no       | `[]`           |
| `edit_strategy` | `"regenerate"` \| `"patch"` | no       | `"regenerate"` |

**Frontend wiring status:** `edit_mode`, `edit_target`, `edit_indices`, and `edit_strategy` are supported by backend schema/graph state but are not yet wired through the primary frontend chat invocation path.

**Response** `200 OK` (`text/event-stream`):

The response is an SSE stream. See section 7.9 for the full event protocol.

**Response headers:**

| Header         | Value                                      |
| -------------- | ------------------------------------------ |
| `Content-Type` | `text/event-stream`                        |
| `X-Thread-ID`  | The chat_id as string (same as path param) |

**Error responses:**

| Status | Detail                      | Cause                            |
| ------ | --------------------------- | -------------------------------- |
| 400    | `"Message cannot be empty"` | Blank or whitespace-only message |
| 401    | `"Invalid Credentials"`     | Missing/expired token            |
| 404    | Chat not found              | Invalid chat_id or wrong owner   |

**Abort behavior:** The client closes the connection (e.g., `reader.cancel()`). The server generator detects the disconnect. The assistant message is left in `"streaming"` or `"pending"` status. On next server startup, stale messages are marked `"failed"` by startup cleanup.

**Side effects:**

1. A `user` message record is created with `status: "completed"`.
2. An `assistant` message record is created with `status: "pending"`, transitions to `"streaming"`, then to `"completed"` or `"failed"`.
3. Events are persisted to the `chat_message_events` table for replay.
4. If `doc_ids` is provided and `chat_router_retrieval_fallback` is enabled, concept-aware retrieval runs before the LLM graph, injecting context as a system message.

---

### GET `/v1/chats/{chat_id}/messages/{message_id}/events`

Replay persisted streaming events for an assistant message.

**Conditional response type:** This endpoint returns different content types depending on the message's current status.

| Message status           | Response type          | Content-Type        |
| ------------------------ | ---------------------- | ------------------- |
| `completed` or `failed`  | JSON body              | `application/json`  |
| `pending` or `streaming` | SSE stream (live tail) | `text/event-stream` |

**Query parameters:**

| Param       | Type | Default | Description                                                                                                                            |
| ----------- | ---- | ------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `after_seq` | int  | 0       | Resume from this sequence number (exclusive). Pass the `last_seq` from a previous response to avoid replaying already-received events. |

**JSON response** (`ChatMessageEventReplayResponse`):

```json
{
  "events": [
    {
      "event_id": "evt-uuid-...",
      "message_id": "msg-uuid-...",
      "seq": 1,
      "event_type": "started",
      "content": null,
      "metadata": { "assistant_message_id": "msg-uuid-..." },
      "created_at": "2026-02-27T10:31:01+00:00"
    },
    {
      "event_id": "evt-uuid-...",
      "message_id": "msg-uuid-...",
      "seq": 2,
      "event_type": "token_chunk",
      "content": "The Krebs cycle is a series of",
      "metadata": null,
      "created_at": "2026-02-27T10:31:02+00:00"
    }
  ],
  "is_complete": true,
  "last_seq": 15
}
```

**SSE response (live tail):** Emits all stored events first, then polls every 500ms for new events until the message reaches a terminal state (`completed` or `failed`). Events follow the same SSE format as the invoke endpoint (see section 7.9).

---

## 7.4 Document Endpoints

Documents belong to users and can be linked to multiple projects. Two routers serve document operations: project-scoped (`/v1/project/{project_id}/documents/`) and user-scoped (`/v1/documents/`).

All document endpoints require `Authorization: Bearer <access_token>`.

### Project-Scoped Document Endpoints (`/v1/project/{project_id}/documents/`)

#### POST `/v1/project/{project_id}/documents/`

Upload documents to a project.

**Request body** (`multipart/form-data`):

| Field   | Type            | Description                 |
| ------- | --------------- | --------------------------- |
| `files` | File[] (binary) | One or more files to upload |

**Allowed file types:**

| Extension | MIME type                                                                 |
| --------- | ------------------------------------------------------------------------- |
| `pdf`     | `application/pdf`                                                         |
| `txt`     | `text/plain`                                                              |
| `doc`     | `application/msword`                                                      |
| `docx`    | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `md`      | `text/markdown`                                                           |

**Max file size:** 10 MB per file.

**Response** `201 Created` (`DocResponse[]`):

```json
[
  {
    "filename": "biology.pdf",
    "file_type": "application/pdf",
    "file_size": 1048576,
    "file_path": "/app/uploads/biology.pdf",
    "file_hash": "a3f2b8c1d4e5...",
    "doc_id": "doc-uuid-...",
    "user_id": "user-uuid-...",
    "project_id": "proj-uuid-...",
    "created_at": "2026-02-27T10:00:00+00:00",
    "updated_at": null,
    "is_embedded": false,
    "embedded_at": null,
    "status": "pending",
    "canonical_document_id": null
  }
]
```

**Dedup behavior:** If a file with the same SHA-256 hash already exists for the user, the existing document is reused and linked to the project rather than creating a duplicate. The `canonical_document_id` field points to the original document when dedup occurs.

---

#### POST `/v1/project/{project_id}/documents/link`

Link existing user-owned documents to a project.

**Request body** (`DocLinkRequest`):

```json
{
  "doc_ids": ["doc-uuid-1", "doc-uuid-2"]
}
```

**Response** `200 OK`:

```json
{
  "linked": 2,
  "skipped": 0
}
```

Idempotent: documents already linked to the project are skipped. Only documents owned by the authenticated user can be linked.

---

#### GET `/v1/project/{project_id}/documents/`

List all documents in a project.

**Response** `200 OK`: `DocResponse[]`

---

#### GET `/v1/project/{project_id}/documents/download`

Download all project documents. Returns a single file if only one document exists, or a ZIP archive if multiple documents exist.

**Response** `200 OK`:

| Scenario       | Content-Type            |
| -------------- | ----------------------- |
| Single file    | Original file MIME type |
| Multiple files | `application/zip`       |

---

#### GET `/v1/project/{project_id}/documents/{doc_id}`

Get a specific document's metadata within a project.

**Response** `200 OK`: `DocResponse`

---

#### DELETE `/v1/project/{project_id}/documents/`

Delete documents entirely (removes from all projects).

**Request body** (`DocDelete`):

```json
{
  "doc_id": ["doc-uuid-1", "doc-uuid-2"]
}
```

Note: The field name is `doc_id` (singular) but accepts a list.

**Response** `200 OK`: Implementation-defined.

---

### User-Scoped Document Endpoints (`/v1/documents/`)

#### GET `/v1/documents/`

List all documents owned by the authenticated user, regardless of project.

**Query parameters:**

| Param   | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `limit` | int  | 50      | Max results |
| `skip`  | int  | 0       | Offset      |

**Response** `200 OK`: `DocResponse[]`

---

#### POST `/v1/documents/`

Upload documents without linking to any project.

**Request body** (`multipart/form-data`): Same as project upload.

**Response** `201 Created`: `DocResponse[]` with `project_id: null`.

---

#### GET `/v1/documents/{doc_id}`

Get a specific document by ID (user-level, no project required).

**Response** `200 OK`: `DocResponse`

---

#### GET `/v1/documents/{doc_id}/download`

Download a single document.

**Response** `200 OK`: File content with original MIME type.

---

#### GET `/v1/documents/{doc_id}/thumbnail`

Get a PNG thumbnail for a document.

**Response** `200 OK`:

| Header         | Value       |
| -------------- | ----------- |
| `Content-Type` | `image/png` |

The server verifies the authenticated user owns the document before returning the thumbnail.

**Behavior details:**

- Thumbnail generation currently supports PDF input only (first page render).
- Output is square PNG (`size x size`, default `512x512`) generated by top-crop + resize.
- Generated thumbnails are cached on disk under `THUMBNAIL_DIR` and reused on subsequent requests.
- Non-PDF documents (or PDF render failures) return an error from the backend helper path.

---

#### DELETE `/v1/documents/`

Delete documents owned by the current user.

**Request body** (`DocDelete`):

```json
{
  "doc_id": ["doc-uuid-1"]
}
```

**Response** `200 OK`: Implementation-defined.

---

## 7.5 Project Endpoints (`/v1/projects/`)

All project endpoints require `Authorization: Bearer <access_token>`.

### POST `/v1/projects/`

Create a new project.

**Request body** (`ProjectBase`):

```json
{
  "project_name": "Biology 101",
  "project_desc": "Notes for intro biology"
}
```

`project_desc` is optional.

**Response** `201 Created` (`ProjectResponse`):

```json
{
  "project_id": "proj-uuid-...",
  "project_name": "Biology 101",
  "project_desc": "Notes for intro biology",
  "created_at": "2026-02-27T10:00:00+00:00",
  "created_by": "user-uuid-..."
}
```

---

### GET `/v1/projects/`

List projects owned by the authenticated user.

**Query parameters:**

| Param   | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `limit` | int  | 50      | Max results |
| `skip`  | int  | 0       | Offset      |

**Response** `200 OK`: `ProjectResponse[]`

---

### GET `/v1/projects/{project_id}`

Get a single project.

**Admin bypass:** Users with `role: "admin"` can access any project. Regular users can only access projects they created. Both cases return 404 (not 403) when access is denied, to avoid leaking project existence.

**Response** `200 OK`: `ProjectResponse`

**Error responses:**

| Status | Detail                                                         | Cause                  |
| ------ | -------------------------------------------------------------- | ---------------------- |
| 404    | `"Project not found"` or `"Project not found or acces denied"` | Not found or not owned |

---

### DELETE `/v1/projects/{project_id}`

Delete a project.

**Response** `200 OK`:

```json
{
  "message": "Project deleted"
}
```

---

## 7.6 Embedding Endpoints (`/v1/embeddings/`)

All embedding endpoints require `Authorization: Bearer <access_token>`.

The embedding system maintains one vectorstore per user. Documents must be synced (embedded) before they can be used for retrieval in chat or agent flows.

### POST `/v1/embeddings/sync`

Trigger embedding of pending documents into the user's vectorstore.

**Request body** (`VectorstoreSyncRequest`, optional):

```json
{
  "doc_ids": ["doc-uuid-1", "doc-uuid-2"]
}
```

If `doc_ids` is omitted or null, all pending (un-embedded) documents for the user are synced.

**Async job semantics:** This endpoint initiates embedding and returns immediately. Use `GET /v1/embeddings/status` to poll for completion.

**Response** `200 OK` (`VectorstoreSyncResponse`):

```json
{
  "status": "processing",
  "message": "Queued 3 documents for embedding",
  "documents_queued": 3,
  "job_id": null
}
```

Idempotent: if all specified documents are already embedded, returns immediately with `documents_queued: 0`.

---

### GET `/v1/embeddings/status`

Get the status of the user's vectorstore.

**Response** `200 OK` (`VectorstoreStatus`):

```json
{
  "user_id": "user-uuid-...",
  "collection_id": "col-uuid-...",
  "status": "ready",
  "total_documents": 5,
  "embedded_documents": 5,
  "pending_documents": 0,
  "last_synced_at": "2026-02-27T10:15:00+00:00",
  "error_message": null
}
```

| `status` value | Meaning                                              |
| -------------- | ---------------------------------------------------- |
| `pending`      | Vectorstore exists but no documents have been synced |
| `processing`   | Embedding is in progress                             |
| `ready`        | All documents are embedded, store is queryable       |
| `failed`       | Last sync failed; check `error_message`              |

---

### DELETE `/v1/embeddings/clear`

Clear the user's vectorstore and reset all documents to un-embedded state.

**Response** `200 OK`:

```json
{
  "message": "Vectorstore cleared"
}
```

**Side effects:**

- All embeddings in the vectorstore are deleted.
- All user documents have `is_embedded` set to `false`.
- Vectorstore status is reset to `"pending"`.
- Documents themselves are not deleted.

Idempotent and safe to call multiple times.

---

## 7.7 MCQ Endpoints (`/v1/mcqs/`)

All MCQ endpoints require `Authorization: Bearer <access_token>`.

### POST `/v1/mcqs/`

Create an MCQ set.

**Request body** (`CreateMCQ`):

```json
{
  "mcq": {
    "questions": [
      {
        "question_id": 1,
        "question": "What is the powerhouse of the cell?",
        "options": [
          { "id": "A", "text": "Nucleus" },
          { "id": "B", "text": "Mitochondria" },
          { "id": "C", "text": "Ribosome" },
          { "id": "D", "text": "Golgi apparatus" }
        ],
        "answer": "B",
        "explanation": "Mitochondria produce ATP through cellular respiration."
      }
    ]
  }
}
```

**Schema constraints:**

- `options[].id` must be one of `"A"`, `"B"`, `"C"`, `"D"`.
- `answer` must be one of `"A"`, `"B"`, `"C"`, `"D"`.

**Response** `201 Created` (`ReadMCQ`):

```json
{
  "mcq": { "questions": [...] },
  "mcq_id": "mcq-uuid-...",
  "generated_at": "2026-02-27T10:30:00+00:00"
}
```

---

### GET `/v1/mcqs/`

List all MCQ sets.

**Response** `200 OK`: `ReadMCQ[]`

Note: This returns all MCQs in the database, not filtered by user. There is no pagination.

---

### GET `/v1/mcqs/download/{id}`

Download an MCQ set as a JSON file.

**Response** `200 OK`:

| Header                | Value                                   |
| --------------------- | --------------------------------------- |
| `Content-Type`        | `application/json`                      |
| `Content-Disposition` | `attachment; filename="mcqs_{id}.json"` |

**Error responses:**

| Status | Detail            | Cause            |
| ------ | ----------------- | ---------------- |
| 404    | `"MCQ not found"` | Invalid MCQ UUID |

Note: The 404 response is returned as a raw `Response(status_code=404, content="MCQ not found")`, not as the standard FastAPI `HTTPException` JSON envelope.

---

## 7.8 Agent/Graph Endpoints (`/v1/graph/`)

These endpoints drive the deprecated RAG/concept-extraction pipeline. Both require `Authorization: Bearer <access_token>`.

**Frontend integration caveat:** The current frontend `agentApi.ts` uses a hardcoded base URL (`http://localhost:8000`) instead of `VITE_API_BASE_URL`, so these endpoints fail in non-local deployments unless the frontend client is changed.

### POST `/v1/graph/start`

Start a new agent graph execution for MCQ generation from selected documents.

**Prerequisite:** The user's vectorstore must be in `"ready"` status (call `POST /v1/embeddings/sync` first, then poll `GET /v1/embeddings/status`).

**Request body** (`StartGraphRequest`):

```json
{
  "doc_ids": ["doc-uuid-1", "doc-uuid-2"],
  "user_prompt": "Generate MCQs about cellular respiration"
}
```

| Field         | Type   | Required | Default                                   |
| ------------- | ------ | -------- | ----------------------------------------- |
| `doc_ids`     | UUID[] | yes      |                                           |
| `user_prompt` | string | no       | `"Generate MCQs from selected documents"` |

**Response** `200 OK` (`text/event-stream`):

**Response headers:**

| Header         | Value                                 |
| -------------- | ------------------------------------- |
| `Content-Type` | `text/event-stream`                   |
| `X-Thread-ID`  | UUID v4 string (needed for `/resume`) |

The stream emits `data:` lines with JSON payloads. See section 7.9 for the event protocol.

**Error responses:**

| Status | Detail                                                                                | Cause                  |
| ------ | ------------------------------------------------------------------------------------- | ---------------------- |
| 400    | `"Vectorstore is not ready. Current status: {status}. Please sync embeddings first."` | Vectorstore not synced |
| 401    | `"Invalid Credentials"`                                                               | Missing/expired token  |

**Human-in-the-loop:** The graph will emit an event with `overview_for_user` data and then interrupt. The stream will end. The client must call `/resume/{thread_id}` with the user's concept selections to continue.

---

### POST `/v1/graph/resume/{thread_id}`

Resume a paused graph execution after concept selection.

**Path parameters:**

| Param       | Type   | Description                                  |
| ----------- | ------ | -------------------------------------------- |
| `thread_id` | string | The `X-Thread-ID` from the `/start` response |

**Request body** (`ResumeRequest`):

```json
{
  "selected_concepts": [
    { "name": "Krebs Cycle", "summary": "Series of chemical reactions..." },
    { "name": "Electron Transport Chain", "summary": "Final stage of..." }
  ]
}
```

**Response** `200 OK` (`text/event-stream`): Continues from where the graph was interrupted. Same SSE event format as `/start`.

**Failure mode:** If the `thread_id` does not correspond to an interrupted graph, the behavior is undefined (depends on LangGraph checkpoint state). There is no explicit validation to return a clean error.

---

## 7.9 SSE Event Protocols

Two distinct SSE protocols exist. Both use `data:` prefix lines with JSON payloads, terminated by double newline (`\n\n`).

### Chat Protocol (used by `/v1/chats/{chat_id}/invoke` and `/v1/chats/{chat_id}/messages/{message_id}/events`)

Each SSE line has the format:

```text
data: {"event": "<type>", ...}\n\n
```

**Event types:**

#### `started`

Emitted once at the beginning of generation.

```json
{
  "event": "started",
  "user_message": {
    "message_id": "...",
    "chat_id": "...",
    "role": "user",
    "sequence": 1,
    "status": "completed",
    "content": "What is photosynthesis?",
    "structured_data": null,
    "doc_ids": [],
    "input_tokens": null,
    "output_tokens": null,
    "error": null,
    "created_at": "2026-02-27T10:31:00+00:00"
  },
  "assistant_message_id": "msg-uuid-..."
}
```

#### `thinking`

Emitted for graph node lifecycle updates (zero or more per generation).

```json
{
  "event": "thinking",
  "node": "intent_classifier",
  "status": "started",
  "label": "Understanding your request\u2026",
  "detail": null
}
```

```json
{
  "event": "thinking",
  "node": "intent_classifier",
  "status": "completed",
  "label": "Understanding your request\u2026",
  "detail": "chat"
}
```

Nodes that emit thinking events: `document_search` (synthetic, only when pre-retrieval runs), `intent_classifier`, `scope_classifier`, `planner`, `retrieval`, `chat_no_tools`, `stem_generator`, `options_generator`.

#### `reasoning_token`

Emitted for chain-of-thought tokens from reasoning models (OpenAI o-series `reasoning_content` or Anthropic `thinking` blocks). Zero or more per generation.

```json
{
  "event": "reasoning_token",
  "content": "Let me think about what photosynthesis involves...",
  "node": "chat_model"
}
```

#### `token`

Emitted for each chunk of the assistant's visible response text.

```json
{
  "event": "token",
  "content": "Photosynthesis is the process"
}
```

Tokens are emitted per-chunk for live responsiveness. For event persistence, tokens are buffered into larger `token_chunk` events (configurable: 50 chars or 200ms, whichever comes first).

#### `done`

Emitted once when generation completes successfully.

```json
{
  "event": "done",
  "assistant_message": {
    "message_id": "...",
    "chat_id": "...",
    "role": "assistant",
    "sequence": 2,
    "status": "completed",
    "content": "Photosynthesis is the process by which...",
    "structured_data": null,
    "doc_ids": [],
    "input_tokens": null,
    "output_tokens": null,
    "error": null,
    "created_at": "2026-02-27T10:31:00+00:00"
  }
}
```

#### `error`

Emitted when generation fails. The stream ends after this event.

```json
{
  "event": "error",
  "detail": "Connection to LLM provider timed out"
}
```

**Persisted event types vs. SSE event types:**

| Persisted `event_type` | SSE `event` field | Notes                                                |
| ---------------------- | ----------------- | ---------------------------------------------------- |
| `started`              | `started`         |                                                      |
| `thinking`             | `thinking`        |                                                      |
| `token_chunk`          | `token`           | Persisted chunks are larger (buffered)               |
| `reasoning_token`      | `reasoning_token` |                                                      |
| `done`                 | `done`            | Persisted version has no `assistant_message` payload |
| `error`                | `error`           | `content` field maps to `detail`                     |

### SSE Event Contract (Backend ↔ Frontend)

Backend constants in `src/api/constants.py` are the canonical persisted vocabulary. Frontend stream parsers consume SSE `event` strings.

| Backend constant        | Persisted `event_type` | SSE `event` value | Frontend parser expectation                               |
| ----------------------- | ---------------------- | ----------------- | --------------------------------------------------------- |
| `EVENT_STARTED`         | `started`              | `started`         | initialize assistant placeholder (`assistant_message_id`) |
| `EVENT_THINKING`        | `thinking`             | `thinking`        | update node status timeline                               |
| `EVENT_TOKEN_CHUNK`     | `token_chunk`          | `token`           | append visible response text chunk                        |
| `EVENT_REASONING_TOKEN` | `reasoning_token`      | `reasoning_token` | append reasoning/thinking chunk                           |
| `EVENT_DONE`            | `done`                 | `done`            | finalize assistant message                                |
| `EVENT_ERROR`           | `error`                | `error`           | surface terminal stream error                             |

**Replay translation source:** `src/api/v1/routers/chat.py::_event_to_sse_line` performs persisted-event to SSE-event translation during replay (`token_chunk -> token`, `thinking -> thinking`, etc.).

---

### Agent Protocol (used by `/v1/graph/start` and `/v1/graph/resume/{thread_id}`)

Each SSE line has the format:

```text
data: {"mode": "custom", "payload": { ... }}\n\n
```

The `mode` field is always `"custom"` (from LangGraph's `stream_mode=["custom"]`).

**Payload event types** (identified by `payload.event`):

#### `node_update`

Emitted for each graph node's lifecycle (started/completed pair).

```json
{
  "mode": "custom",
  "payload": {
    "event": "node_update",
    "node": "fetch_documents",
    "status": "started",
    "label": "Reading your documents\u2026"
  }
}
```

```json
{
  "mode": "custom",
  "payload": {
    "event": "node_update",
    "node": "fetch_documents",
    "status": "completed",
    "label": "Reading your documents\u2026",
    "detail": "Read 3 document(s)"
  }
}
```

**Known node names and their labels:**

| Node                 | Label                                        | Detail (on completed)             |
| -------------------- | -------------------------------------------- | --------------------------------- |
| `guardrail`          | "Checking your request..."                   | "Looking good, let's go"          |
| `query_generation`   | "Figuring out what to look for..."           | "Found {N} angles to explore"     |
| `retrieval`          | "Searching your documents..."                | "Pulled {N} relevant passages"    |
| `mcq_generation`     | "Drafting questions from what I found..."    | "Questions ready"                 |
| `chat_generation`    | "Thinking about your question..."            | "Done thinking"                   |
| `fetch_documents`    | "Reading your documents..."                  | "Read {N} document(s)"            |
| `generate_summaries` | "Picking out the key concepts..."            | "Found concepts across your docs" |
| `search_queries`     | "Building search queries for your topics..." | "Created {N} search queries"      |
| `search_queries_v2`  | "Building search queries for your topics..." | "Created {N} search queries"      |

#### Human-in-the-loop interrupt

The `generate_summaries` node's completed event includes an `overview` field with extracted concepts. The graph then interrupts (via LangGraph's `interrupt()`), causing the SSE stream to end. The payload shape on the completed event for `generate_summaries`:

```json
{
  "mode": "custom",
  "payload": {
    "event": "node_update",
    "node": "generate_summaries",
    "status": "completed",
    "label": "Picking out the key concepts\u2026",
    "detail": "Found concepts across your docs",
    "overview": [
      {
        "doc_name": "biology.pdf",
        "concepts": [
          { "name": "Krebs Cycle", "summary": "..." },
          { "name": "Glycolysis", "summary": "..." }
        ]
      }
    ]
  }
}
```

The interruption itself produces an `interrupt` payload from LangGraph's checkpoint system. The client should present the concepts to the user and call `POST /v1/graph/resume/{thread_id}` with the selected subset.

**GAP:** Agent SSE event types are not formally defined in any schema. The event vocabulary is determined by `writer()` calls inside agent node implementations. Adding a new node with a new `writer()` call will introduce new events without any schema change.

---

## 7.10 Error Response Format

### Standard error shape

All `HTTPException` responses from FastAPI follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Pydantic validation errors (422)

Request body validation failures return:

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long",
      "type": "value_error"
    }
  ]
}
```

### Status code semantics

| Code | Meaning                                                                                                   |
| ---- | --------------------------------------------------------------------------------------------------------- |
| 400  | Validation error at business-logic level (e.g., duplicate email, empty message, vectorstore not ready)    |
| 401  | Authentication failed (missing token, expired token, bad credentials)                                     |
| 403  | Not used in current codebase; access denial returns 404 instead                                           |
| 404  | Resource not found or user does not have access (used for both cases to avoid leaking resource existence) |
| 409  | Conflict (e.g., email already in use during edit)                                                         |
| 422  | Pydantic schema validation failure                                                                        |
| 500  | Unhandled server error (refresh token generation failure, database errors)                                |

### Known inconsistencies

1. The MCQ download endpoint (`GET /v1/mcqs/download/{id}`) returns 404 as a raw `Response(status_code=404, content="MCQ not found")` with `text/plain` content type instead of the standard `{ "detail": "..." }` JSON envelope.
2. Some CRUD functions raise `HTTPException(status_code=400, ...)` for what is semantically a 409 conflict (e.g., `create_user` raises 400 for duplicate email).
3. Error codes are not enumerated in a central location. Each router/CRUD function defines its own error messages inline.
4. SSE stream errors are delivered as `data: {"event": "error", "detail": "..."}` inside the stream, not as HTTP status codes (since the connection is already 200 OK when the error occurs).

---

## Things a first-time contributor would likely misunderstand

1. **Login uses form-encoded data, not JSON.** The `POST /v1/auth/login` endpoint expects `application/x-www-form-urlencoded` with a `username` field (not `email`), because it uses FastAPI's `OAuth2PasswordRequestForm`. Every other mutation endpoint uses JSON. Sending JSON to `/login` returns a 422 with no obvious explanation.

2. **The events endpoint has two return types.** `GET /v1/chats/{chat_id}/messages/{message_id}/events` returns either `application/json` or `text/event-stream` depending on the message's status at query time. A client that assumes one content type will break on the other. The frontend handles this by checking the `Content-Type` response header and branching.

3. **Persisted event types differ from SSE event names.** The `token_chunk` event type in the database maps to a `token` event in the SSE stream. The `done` event in the database has no `assistant_message` payload, but the live SSE `done` event does. Code that replays persisted events must translate between these schemas (see `_event_to_sse_line` in the chat router).
